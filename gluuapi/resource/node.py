# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import uuid
from glob import iglob

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource

from ..database import db
from ..reqparser import NodeReq
from ..model import STATE_IN_PROGRESS
from ..model import STATE_SUCCESS
from ..helper import LdapModelHelper
from ..helper import OxauthModelHelper
from ..helper import OxtrustModelHelper
from ..helper import OxidpModelHelper
from ..helper import NginxModelHelper
from ..helper import HttpdModelHelper
from ..model import LdapNode
from ..model import OxauthNode
from ..model import OxtrustNode
from ..model import OxidpNode
from ..model import NginxNode


class NodeResource(Resource):
    helper_classes = {
        "ldap": LdapModelHelper,
        "oxauth": OxauthModelHelper,
        "oxtrust": OxtrustModelHelper,
        "oxidp": OxidpModelHelper,
        "nginx": NginxModelHelper,
        "httpd": HttpdModelHelper,
    }

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

        teardown_log = "{}-teardown.log".format(node.name)
        logpath = os.path.join(app.config["LOG_DIR"], teardown_log)

        # run the teardown process
        helper_class = self.helper_classes[node.type]
        helper = helper_class(node, app, logpath)
        helper.teardown()

        headers = {
            "X-Gluu-Teardown-Log": url_for("nodelogresource", logpath=teardown_log, _external=True),
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
        obj_list = db.all("nodes")
        return [item.as_dict() for item in obj_list]

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

        # TODO: perhaps it's better move the logic to reqparser/node.py
        if node_type == "oxtrust":
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

        # TODO: perhaps it's better move the logic to reqparser/node.py
        if node_type == "nginx":
            nginx_num = len(provider.get_node_objects(type_="nginx"))
            if nginx_num:
                # only allow 1 nginx per provider
                return {
                    "status": 403,
                    "message": "cannot deploy additional nginx node to specified provider",
                }, 403

        # TODO: perhaps it's better move the logic to reqparser/node.py
        if node_type == "ldap":
            if len(cluster.get_ldap_objects()) >= 4:
                # only allow 4 ldap per cluster
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

        setup_log = "{}-setup.log".format(node.name)
        logpath = os.path.join(app.config["LOG_DIR"], setup_log)

        # run the setup process
        helper_class = self.helper_classes[params["node_type"]]
        helper = helper_class(node, app, logpath)
        helper.setup(params["connect_delay"], params["exec_delay"])

        headers = {
            "X-Deploy-Log": logpath,  # deprecated in favor of X-Gluu-Setup-Log
            "X-Gluu-Setup-Log": url_for("nodelogresource", logpath=setup_log, _external=True),
            "Location": url_for("noderesource", node_id=node.name),
        }
        return node.as_dict(), 202, headers


class NodeLogResource(Resource):
    def get(self, logpath):
        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["LOG_DIR"], logpath)

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
        app = current_app._get_current_object()
        log_dir = app.config["LOG_DIR"]

        setup_logs = iglob("{}/*-setup.log".format(log_dir))
        teardown_logs = iglob("{}/*-teardown.log".format(log_dir))
        logs = list(setup_logs) + list(teardown_logs)

        return [log.replace(log_dir + "/", "") for log in logs]
