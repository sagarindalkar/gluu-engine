# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from flask import abort
from flask import current_app
from flask.ext.restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.helper.model_helper import LdapModelHelper
from gluuapi.helper.model_helper import OxAuthModelHelper
from gluuapi.helper.model_helper import OxTrustModelHelper
from gluuapi.helper.docker_helper import DockerHelper
from gluuapi.helper.salt_helper import SaltHelper
from gluuapi.reqparser import node_req
from gluuapi.setup.oxauth_setup import OxAuthSetup
from gluuapi.setup.oxtrust_setup import OxTrustSetup
from gluuapi.setup.ldap_setup import ldapSetup


class Node(Resource):
    @swagger.operation(
        notes='Gives a node info/state',
        nickname='getnode',
        parameters=[],
        responseMessages=[
            {
              "code": 200,
              "message": "Node information",
            },
            {
                "code": 404,
                "message": "Node not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary='TODO'
    )
    def get(self, node_id):
        obj = db.get(node_id, "nodes")
        if not obj:
            return {"code": 404, "message": "Node not found"}, 404
        return obj.as_dict()

    @swagger.operation(
        notes='delete a node',
        nickname='delnode',
        parameters=[],
        responseMessages=[
            {
              "code": 204,
              "message": "Node deleted",
            },
            {
                "code": 404,
                "message": "Node not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='TODO'
    )
    def delete(self, node_id):
        node = db.get(node_id, "nodes")

        if not node:
            return {"code": 404, "message": "Node not found"}, 404

        cluster = db.get(node.cluster_id, "clusters")
        provider = db.get(node.provider_id, "providers")

        if node.type == "ldap":
            setup_obj = ldapSetup(node, cluster)
            setup_obj.stop()

        # remove container
        docker = DockerHelper(base_url=provider.base_url)
        docker.remove_container(node.id)

        # unregister minion
        salt_helper = SaltHelper()
        salt_helper.unregister_minion(node.id)

        # remove node
        db.delete(node_id, "nodes")

        # removes reference from cluster, if any
        cluster.remove_node(node)
        db.update(cluster.id, cluster, "clusters")

        # TODO: move to helper?
        if node.type == "ldap":
            # Currently, we need to update oxAuth and oxTrust LDAP properties
            # TODO: use signals?
            for oxauth_node_id in cluster.oxauth_nodes:
                oxauth_node = db.get(oxauth_node_id, "nodes")
                if not oxauth_node:
                    continue

                setup_obj = OxAuthSetup(oxauth_node, cluster)
                setup_obj.render_ldap_props_template()

            for oxtrust_node_id in cluster.oxtrust_nodes:
                oxtrust_node = db.get(oxtrust_node_id, "nodes")
                if not oxtrust_node:
                    continue

                setup_obj = OxTrustSetup(oxtrust_node, cluster)
                setup_obj.render_ldap_props_template()
        return {}, 204


class NodeList(Resource):
    @swagger.operation(
        notes='Gives node list info/state',
        nickname='listnode',
        parameters=[],
        responseMessages=[
            {
              "code": 200,
              "message": "List node information",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary='TODO'
    )
    def get(self):
        obj_list = db.all("nodes")
        return [item.as_dict() for item in obj_list]

    @swagger.operation(
        notes="""This API will create a new Gluu Server cluster node. This may take a while, so the process
is handled asyncronously by the Twisted reactor. It includes creating a new docker instance, deploying
the necessary software components, and updating the configuration of the target node and any
other dependent cluster nodes. Subsequent GET requests will be necessary to find out when the
status of the cluster node is available.""",
        nickname='postnode',
        parameters=[
            {
                "name": "cluster",
                "description": "The ID of the cluster",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "node_type",
                "description": "one of 'ldap', 'oxauth', or 'oxtrust'",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "provider_id",
                "description": "The ID of the provider",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
        ],
        responseMessages=[
            {
                "code": 202,
                "message": "Accepted",
            },
            {
                "code": 400,
                "message": "Bad Request",
            },
            {
                "code": 403,
                "message": "Forbidden",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary='TODO'
    )
    def post(self):
        params = node_req.parse_args()
        salt_master_ipaddr = current_app.config["SALT_MASTER_IPADDR"]

        # check node type
        if params.node_type not in ("ldap", "oxauth", "oxtrust"):
            abort(400)

        # check that cluster ID is valid else return with message and code
        cluster = db.get(params.cluster, "clusters")
        if not cluster:
            return {"code": 400, "message": "invalid cluster ID"}, 400

        # check that provider ID is valid else return with message and code
        provider = db.get(params.provider_id, "providers")
        if not provider:
            return {"code": 400, "message": "invalid provider ID"}, 400

        if params.node_type == "ldap":
            # checks if this new node will exceed max. allowed LDAP nodes
            if len(cluster.ldap_nodes) + 1 > cluster.max_allowed_ldap_nodes:
                return {"code": 403, "message": "max. allowed LDAP nodes is reached"}, 403
            helper_class = LdapModelHelper
        elif params.node_type == "oxauth":
            helper_class = OxAuthModelHelper
        elif params.node_type == "oxtrust":
            helper_class = OxTrustModelHelper

        helper = helper_class(cluster, provider, salt_master_ipaddr)
        print "build logpath: %s" % helper.logpath
        helper.setup()
        return {}, 202
