# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource
from flask_restful_swagger import swagger
from requests.exceptions import SSLError

from ..database import db
from ..reqparser import NodeReq
from ..model import STATE_IN_PROGRESS
from ..model import STATE_SUCCESS
from ..helper import DockerHelper
from ..helper import SaltHelper
from ..helper import PrometheusHelper
from ..helper import LdapModelHelper
from ..helper import OxauthModelHelper
from ..helper import OxtrustModelHelper
from ..helper import HttpdModelHelper
from ..helper import SamlModelHelper
from ..helper import distribute_cluster_data
from ..setup import LdapSetup
from ..setup import HttpdSetup
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import SamlSetup


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
        summary='Get existing provider',
    )
    def get(self, node_id):
        try:
            node = db.search_from_table(
                "nodes",
                (db.where("id") == node_id) | (db.where("name") == node_id),
            )[0]
        except IndexError:
            node = None

        if not node:
            return {"status": 404, "message": "Node not found"}, 404
        return node.as_dict()

    @swagger.operation(
        notes='delete a node',
        nickname='delnode',
        parameters=[
            {
                "name": "force",
                "description": "Force delete",
                "required": False,
                "dataType": "string",
                "paramType": "query",
            },
        ],
        responseMessages=[
            {
                "code": 204,
                "message": "Node deleted",
            },
            {
                "code": 403,
                "message": "Forbidden",
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
        summary='Delete existing node',
    )
    def delete(self, node_id):
        template_dir = current_app.config["TEMPLATES_DIR"]
        truthy = ("1", "True", "true", "t",)
        falsy = ("0", "false", "False", "f",)

        force_delete = request.args.get("force", False)

        if force_delete in falsy:
            force_delete = False
        elif force_delete in truthy:
            force_delete = True
        else:
            force_delete = False

        try:
            node = db.search_from_table(
                "nodes",
                (db.where("id") == node_id) | (db.where("name") == node_id),
            )[0]
        except IndexError:
            node = None

        if not node:
            return {"status": 404, "message": "Node not found"}, 404

        # if not a force-delete, node with state set to IN_PROGRESS
        # must not be deleted
        if node.state == STATE_IN_PROGRESS and force_delete is False:
            return {
                "status": 403,
                "message": "cannot delete node while still in deployment",
            }, 403

        # remove node (``node.id`` may empty, hence we're using
        # unique ``node.name`` instead)
        db.delete_from_table("nodes", db.where("name") == node.name)

        cluster = db.get(node.cluster_id, "clusters")
        provider = db.get(node.provider_id, "providers")

        if node.type == "ldap":
            setup_obj = LdapSetup(node, cluster, template_dir=template_dir)
        elif node.type == "httpd":
            setup_obj = HttpdSetup(node, cluster, template_dir=template_dir)
        elif node.type == "oxauth":  # pragma: no cover
            setup_obj = OxauthSetup(node, cluster, template_dir=template_dir)
        elif node.type == "oxtrust":  # pragma: no cover
            setup_obj = OxtrustSetup(node, cluster, template_dir=template_dir)
        elif node.type == "saml":  # pragma: no cover
            setup_obj = SamlSetup(node, cluster, template_dir=template_dir)
        setup_obj.teardown()

        docker = DockerHelper(provider)
        salt = SaltHelper()

        try:
            docker.remove_container(node.name)
        except SSLError:  # pragma: no cover
            current_app.logger.warn("unable to connect to docker API "
                                    "due to SSL connection errors")
        salt.unregister_minion(node.id)

        # updating prometheus
        prometheus = PrometheusHelper(template_dir=template_dir)
        prometheus.update()
        distribute_cluster_data(current_app.config["DATABASE_URI"])
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
        summary='Get a list of existing nodes',
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
                "name": "cluster_id",
                "description": "The ID of the cluster",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "node_type",
                "description": "one of 'ldap', 'oxauth', 'oxtrust', or 'httpd'",
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
            {
                "name": "connect_delay",
                "description": "Time to wait (in seconds) before start connecting to node (default to 10 seconds).",
                "required": False,
                "dataType": "integer",
                "paramType": "form",
            },
            {
                "name": "exec_delay",
                "description": "Time to wait (in seconds) before start executing command in node (default to 15 seconds).",
                "required": False,
                "dataType": "integer",
                "paramType": "form",
            },
            {
                "name": "oxauth_node_id",
                "description": "ID of oxauth node (required when deploying httpd node).",
                "required": False,
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
        summary='Create a new node',
    )
    def post(self):
        node_type = request.form.get("node_type", "")
        ctx = {"node_type": node_type}
        data, errors = NodeReq(context=ctx).load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid params",
                "params": errors,
            }, 400

        salt_master_ipaddr = current_app.config["SALT_MASTER_IPADDR"]
        template_dir = current_app.config["TEMPLATES_DIR"]
        log_dir = current_app.config["LOG_DIR"]
        database_uri = current_app.config["DATABASE_URI"]
        cluster = data["context"]["cluster"]
        provider = data["context"]["provider"]
        params = data["params"]

        if params["node_type"] == "oxtrust":
            # only allow 1 oxtrust per cluster
            oxtrust_num = db.count_from_table(
                "nodes",
                (db.where("type") == "oxtrust") & (db.where("state") == STATE_SUCCESS),
            )
            if oxtrust_num:
                return {
                    "status": 403,
                    "message": "cannot deploy additional oxtrust node to cluster",
                }, 403
            if provider.type != "master":
                return {
                    "status": 403,
                    "message": "cannot deploy oxtrust node to non-master provider",
                }, 403

        addr, prefixlen = cluster.reserve_ip_addr()
        cluster.last_fetched_addr = addr
        db.update(cluster.id, cluster, "clusters")

        helper_classes = {
            "ldap": LdapModelHelper,
            "oxauth": OxauthModelHelper,
            "oxtrust": OxtrustModelHelper,
            "httpd": HttpdModelHelper,
            "saml": SamlModelHelper,
        }
        helper_class = helper_classes[params["node_type"]]

        helper = helper_class(cluster, provider, salt_master_ipaddr,
                              template_dir, log_dir, database_uri)

        if helper.node.type == "httpd":
            helper.node.oxauth_node_id = params["oxauth_node_id"]
            helper.node.saml_node_id = params["saml_node_id"]

        helper.setup(params["connect_delay"], params["exec_delay"])

        headers = {
            "X-Deploy-Log": helper.logpath,
            "Location": url_for("node", node_id=helper.node.name),
        }
        # for render purpose, we set the state as in-progress
        helper.node.state = STATE_IN_PROGRESS
        return helper.node.as_dict(), 202, headers
