# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import uuid

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource

from ..database import db
from ..reqparser import NodeReq
from ..model import STATE_IN_PROGRESS
from ..helper import LdapModelHelper
from ..helper import OxauthModelHelper
from ..helper import OxtrustModelHelper
from ..helper import OxidpModelHelper
from ..helper import NginxModelHelper
from ..model import LdapNode
from ..model import OxauthNode
from ..model import OxtrustNode
from ..model import OxidpNode
from ..model import NginxNode
from ..model import NodeLog


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
    helper_classes = {
        "ldap": LdapModelHelper,
        "oxauth": OxauthModelHelper,
        "oxtrust": OxtrustModelHelper,
        "oxidp": OxidpModelHelper,
        "nginx": NginxModelHelper,
    }

    def get(self, node_id):
        node = get_node(db, node_id)

        if not node:
            return {"status": 404, "message": "Node not found"}, 404
        return node.as_dict()

    def delete(self, node_id):
        app = current_app._get_current_object()

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

        node_log = NodeLog.create_or_get(node)
        logpath = os.path.join(app.config["LOG_DIR"], node_log.teardown_log)

        # run the teardown process
        helper_class = self.helper_classes[node.type]
        helper = helper_class(node, app, logpath)
        helper.teardown()

        headers = {
            "X-Node-Teardown-Log": url_for(
                "nodelogteardownresource",
                id=node_log.id,
                _external=True,
            ),
        }
        return {}, 204, headers


class NodeListResource(Resource):
    helper_classes = {
        "ldap": LdapModelHelper,
        "oxauth": OxauthModelHelper,
        "oxtrust": OxtrustModelHelper,
        "oxidp": OxidpModelHelper,
        "nginx": NginxModelHelper,
    }

    node_classes = {
        "ldap": LdapNode,
        "oxauth": OxauthNode,
        "oxtrust": OxtrustNode,
        "oxidp": OxidpNode,
        "nginx": NginxNode,
    }

    def get(self):
        nodes = db.all("nodes")
        return [node.as_dict() for node in nodes]

    def post(self):
        app = current_app._get_current_object()
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

        # pre-populate the node object
        node_class = self.node_classes[params["node_type"]]
        node = node_class()
        node.cluster_id = cluster.id
        node.provider_id = provider.id
        node.name = "{}_{}".format(node.image, uuid.uuid4())

        # set the weave IP immediately to prevent race condition
        # when nodes are requested concurrently
        node.weave_ip = addr
        node.weave_prefixlen = prefixlen
        node.state = STATE_IN_PROGRESS
        db.persist(node, "nodes")

        # log related setup
        node_log = NodeLog.create_or_get(node)

        logpath = os.path.join(app.config["LOG_DIR"], node_log.setup_log)

        # run the setup process
        helper_class = self.helper_classes[params["node_type"]]
        helper = helper_class(node, app, logpath)
        helper.setup(params["connect_delay"], params["exec_delay"])

        headers = {
            "X-Deploy-Log": logpath,  # deprecated in favor of X-Gluu-Setup-Log
            "X-Node-Setup-Log": url_for(
                "nodelogsetupresource",
                id=node_log.id,
                _external=True,
            ),
            "Location": url_for("noderesource", node_id=node.name),
        }
        return node.as_dict(), 202, headers


class NodeLogResource(Resource):
    def get(self, id):
        node_log = db.get(id, "node_logs")
        if not node_log:
            return {"status": 404, "message": "Node log not found"}, 404
        return node_log.as_dict()

    def delete(self, id):
        node_log = db.get(id, "node_logs")
        if not node_log:
            return {"status": 404, "message": "Node log not found"}, 404

        db.delete(id, "node_logs")

        app = current_app._get_current_object()
        abs_setup_log = os.path.join(app.config["LOG_DIR"],
                                     node_log.setup_log)
        abs_teardown_log = os.path.join(app.config["LOG_DIR"],
                                        node_log.teardown_log)

        # cleanup unused logs
        for log in [abs_setup_log, abs_teardown_log]:
            try:
                os.unlink(log)
            except OSError:
                pass
        return {}, 204


class NodeLogSetupResource(Resource):
    def get(self, id):
        node_log = db.get(id, "node_logs")
        if not node_log:
            return {"status": 404, "message": "Node setup log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["LOG_DIR"], node_log.setup_log)

        try:
            with open(abs_logpath) as fp:
                return [line.strip() for line in fp]
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class NodeLogTeardownResource(Resource):
    def get(self, id):
        node_log = db.get(id, "node_logs")
        if not node_log:
            return {"status": 404, "message": "Node teardown log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["LOG_DIR"],
                                   node_log.teardown_log)

        try:
            with open(abs_logpath) as fp:
                return [line.strip() for line in fp]
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class NodeLogListResource(Resource):
    def get(self):
        node_logs = db.all("node_logs")
        return [node_log.as_dict() for node_log in node_logs]
