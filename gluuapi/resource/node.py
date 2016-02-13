# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource
from requests.exceptions import SSLError

from ..database import db
from ..reqparser import NodeReq
from ..model import STATE_IN_PROGRESS
from ..model import STATE_FAILED
from ..helper import DockerHelper
from ..helper import SaltHelper
from ..helper import PrometheusHelper
from ..helper import LdapModelHelper
from ..helper import OxauthModelHelper
from ..helper import OxtrustModelHelper
from ..helper import OxidpModelHelper
from ..helper import NginxModelHelper
from ..helper import OxasimbaModelHelper
from ..helper import distribute_cluster_data
from ..setup import LdapSetup
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import OxidpSetup
from ..setup import NginxSetup
from ..setup import OxasimbaSetup


def get_node(db, node_id):
    try:
        node = db.search_from_table(
            "nodes",
            (db.where("id") == node_id) | (db.where("name") == node_id),
        )[0]
    except IndexError:
        node = None
    return node


class NodeResource(Resource):
    def get(self, node_id):
        node = get_node(db, node_id)

        if not node:
            return {"status": 404, "message": "Node not found"}, 404
        return node.as_dict()

    def delete(self, node_id):
        truthy = ("1", "True", "true", "t",)
        falsy = ("0", "false", "False", "f",)

        force_delete = request.args.get("force_rm", False)

        if force_delete in falsy:
            force_delete = False
        elif force_delete in truthy:
            force_delete = True
        else:
            force_delete = False

        # get node object
        node = get_node(db, node_id)

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
        app = current_app._get_current_object()

        # only do teardown on node with SUCCESS, DISABLED, IN_PROGRESS status;
        # this means we don't need to do teardown on FAILED node
        # as FAILED node (mostly) is not attached into the cluster
        if node.state != STATE_FAILED:
            setup_classes = {
                "ldap": LdapSetup,
                "oxauth": OxauthSetup,
                "oxtrust": OxtrustSetup,
                "oxidp": OxidpSetup,
                "nginx": NginxSetup,
                "oxasimba": OxasimbaSetup,
            }
            setup_cls = setup_classes.get(node.type)
            if setup_cls:
                setup_cls(node, cluster, app).teardown()

        docker = DockerHelper(provider)
        salt = SaltHelper()

        try:
            docker.remove_container(node.name)
        except SSLError:  # pragma: no cover
            current_app.logger.warn("unable to connect to docker API "
                                    "due to SSL connection errors")
        salt.unregister_minion(node.id)

        # updating prometheus
        prometheus = PrometheusHelper(current_app._get_current_object())
        prometheus.update()
        distribute_cluster_data(current_app.config["DATABASE_URI"])

        # remove node's log file
        try:
            os.unlink(node.setup_logpath)
        except OSError:
            pass
        return {}, 204


class NodeListResource(Resource):
    helper_classes = {
        "ldap": LdapModelHelper,
        "oxauth": OxauthModelHelper,
        "oxtrust": OxtrustModelHelper,
        "oxidp": OxidpModelHelper,
        "nginx": NginxModelHelper,
        "oxasimba": OxasimbaModelHelper,
    }

    def get(self):
        obj_list = db.all("nodes")
        return [item.as_dict() for item in obj_list]

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

        cluster = data["context"]["cluster"]
        provider = data["context"]["provider"]
        params = data["params"]

        # only allow 1 oxtrust node per cluster
        if node_type == "oxtrust" and cluster.count_node_objects(type_="oxtrust"):
            return {
                "status": 403,
                "message": "cannot deploy additional oxtrust node "
                           "to cluster",
            }, 403

        # only allow oxtrust node in master provider
        if node_type == "oxtrust" and provider.type != "master":
            return {
                "status": 403,
                "message": "cannot deploy oxtrust node "
                           "to non-master provider",
            }, 403

        # only allow 1 nginx per provider
        if node_type == "nginx" and provider.count_node_objects(type_="nginx"):
            return {
                "status": 403,
                "message": "cannot deploy additional nginx node "
                           "to specified provider",
            }, 403

        # only allow 4 ldap per cluster
        if node_type == "ldap" and cluster.count_node_objects(type_="ldap") >= 4:
            return {
                "status": 403,
                "message": "cannot deploy additional ldap node to cluster",
            }, 403

        addr, prefixlen = cluster.reserve_ip_addr()
        if not addr:
            return {
                "status": 403,
                "message": "cluster is running out of weave IP",
            }, 403

        helper_class = self.helper_classes[params["node_type"]]
        helper = helper_class(cluster, provider,
                              current_app._get_current_object())

        # set the weave IP immediately to prevent race condition
        # when nodes are requested concurrently
        helper.node.weave_ip = addr
        helper.node.weave_prefixlen = prefixlen
        helper.node.state = STATE_IN_PROGRESS
        db.persist(helper.node, "nodes")

        helper.setup(params["connect_delay"], params["exec_delay"])

        headers = {
            "X-Deploy-Log": helper.logpath,
            "Location": url_for("noderesource", node_id=helper.node.name),
        }
        return helper.node.as_dict(), 202, headers
