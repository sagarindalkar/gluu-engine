# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import time
import uuid

from flask import abort
from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource

from ..database import db
from ..reqparser import ContainerReq
from ..model import STATE_IN_PROGRESS
from ..model import STATE_SETUP_IN_PROGRESS
from ..model import STATE_TEARDOWN_IN_PROGRESS
from ..helper import LdapContainerHelper
from ..helper import OxauthContainerHelper
from ..helper import OxtrustContainerHelper
from ..helper import OxidpContainerHelper
from ..helper import NginxContainerHelper
from ..helper import OxasimbaContainerHelper
from ..model import LdapContainer
from ..model import OxauthContainer
from ..model import OxtrustContainer
from ..model import OxidpContainer
from ..model import NginxContainer
from ..model import OxasimbaContainer
from ..model import ContainerLog
from ..machine import Machine


#: List of supported container
CONTAINER_CHOICES = (
    "ldap",
    "oxauth",
    "oxtrust",
    "oxidp",
    "nginx",
    # "oxasimba",
)


def get_container(db, container_id):
    try:
        container = db.search_from_table(
            "containers",
            {"$or": [{"id": container_id}, {"name": container_id}]},
        )[0]
    except IndexError:
        container = None
    return container


def target_node_reachable(node_name):
    return Machine().status(node_name)


def master_node_reachable():
    try:
        node = db.search_from_table(
            "nodes", {"type": "master"},
        )[0]
    except IndexError:
        return False
    else:
        return Machine().status(node.name)


def discovery_node_reachable():
    try:
        node = db.search_from_table(
            "nodes", {"type": "discovery"},
        )[0]
    except IndexError:
        return False
    else:
        return Machine().status(node.name)


class ContainerResource(Resource):
    helper_classes = {
        "ldap": LdapContainerHelper,
        "oxauth": OxauthContainerHelper,
        "oxtrust": OxtrustContainerHelper,
        "oxidp": OxidpContainerHelper,
        "nginx": NginxContainerHelper,
        "oxasimba": OxasimbaContainerHelper,
    }

    def get(self, container_id):
        container = get_container(db, container_id)

        if not container:
            return {"status": 404, "message": "Container not found"}, 404
        return container.as_dict()

    def delete(self, container_id):
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

        # get container object
        container = get_container(db, container_id)

        if not container:
            return {"status": 404, "message": "Container not found"}, 404

        # if not a force-delete, container with state set to IN_PROGRESS
        # must not be deleted
        if container.state == STATE_IN_PROGRESS and force_delete is False:
            return {
                "status": 403,
                "message": "cannot delete container while still in deployment",
            }, 403

        node = db.get(container.node_id, "nodes")

        # reject request if target node is unreachable
        if not target_node_reachable(node.name):
            return {
                "status": 403,
                "message": "access denied due to target node being unreachable",
            }, 403

        # reject request if master node is unreachable
        if not master_node_reachable():
            return {
                "status": 403,
                "message": "access denied due to master node being unreachable",
            }, 403

        # reject request if discovery node is unreachable, otherwise docker
        # connection will be stuck
        if not discovery_node_reachable():
            return {
                "status": 403,
                "message": "access denied due to discovery node being unreachable",
            }, 403

        # remove container (``container.id`` may empty, hence we're using
        # unique ``container.name`` instead)
        db.delete_from_table("containers", {"name": container.name})

        container_log = ContainerLog.create_or_get(container)
        container_log.state = STATE_TEARDOWN_IN_PROGRESS
        container_log.teardown_log_url = url_for(
            "containerlog_teardown",
            id=container_log.id,
            _external=True,
        )
        time.sleep(1)
        db.update(container_log.id, container_log, "container_logs")

        logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                               container_log.teardown_log)

        # run the teardown process
        helper_class = self.helper_classes[container.type]
        helper = helper_class(container, app, logpath)
        helper.teardown()

        headers = {
            "X-Container-Teardown-Log": container_log.teardown_log_url,
        }
        return {}, 204, headers


class ContainerListResource(Resource):
    def get(self, container_type=""):
        if not container_type:
            containers = db.all("containers")
            return [container.as_dict() for container in containers]

        if container_type not in CONTAINER_CHOICES:
            abort(404)

        containers = db.search_from_table(
            "containers", {"type": container_type},
        )
        return [container.as_dict() for container in containers]


class NewContainerResource(Resource):
    helper_classes = {
        "ldap": LdapContainerHelper,
        "oxauth": OxauthContainerHelper,
        "oxtrust": OxtrustContainerHelper,
        "oxidp": OxidpContainerHelper,
        "nginx": NginxContainerHelper,
        "oxasimba": OxasimbaContainerHelper,
    }

    container_classes = {
        "ldap": LdapContainer,
        "oxauth": OxauthContainer,
        "oxtrust": OxtrustContainer,
        "oxidp": OxidpContainer,
        "nginx": NginxContainer,
        "oxasimba": OxasimbaContainer,
    }

    def post(self, container_type):
        app = current_app._get_current_object()

        if container_type not in CONTAINER_CHOICES:
            abort(404)

        data, errors = ContainerReq().load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid params",
                "params": errors,
            }, 400

        try:
            cluster = db.all("clusters")[0]
        except IndexError:
            return {
                "status": 403,
                "message": "container deployment requires a cluster",
            }, 403

        node = data["context"]["node"]

        # reject request if target node is unreachable
        if not target_node_reachable(node.name):
            return {
                "status": 403,
                "message": "access denied due to target node being unreachable",
            }, 403

        # reject request if master node is unreachable
        if not master_node_reachable():
            return {
                "status": 403,
                "message": "access denied due to master node being unreachable",
            }, 403

        # reject request if discovery node is unreachable, otherwise docker
        # connection will be stuck
        if not discovery_node_reachable():
            return {
                "status": 403,
                "message": "access denied due to discovery node being unreachable",
            }, 403

        # only allow 1 oxtrust per cluster
        if container_type == "oxtrust" and cluster.count_containers(type_="oxtrust"):
            return {
                "status": 403,
                "message": "cannot deploy additional oxtrust container "
                           "to cluster",
            }, 403

        # only allow oxtrust in master node
        if container_type == "oxtrust" and node.type != "master":
            return {
                "status": 403,
                "message": "cannot deploy oxtrust container "
                           "to non-master node",
            }, 403

        # only allow 1 nginx per node
        if container_type == "nginx" and node.count_containers(type_="nginx"):
            return {
                "status": 403,
                "message": "cannot deploy additional nginx container "
                           "to specified node",
            }, 403

        # only allow 1 ldap per node
        if container_type == "ldap" and node.count_containers(type_="ldap"):
            return {
                "status": 403,
                "message": "cannot deploy additional ldap container "
                           "to specified node",
            }, 403

        # addr, prefixlen = cluster.reserve_ip_addr()
        # if not addr:
        #     return {
        #         "status": 403,
        #         "message": "cluster is running out of weave IP",
        #     }, 403

        # pre-populate the container object
        container_class = self.container_classes[container_type]
        container = container_class()
        container.cluster_id = cluster.id
        container.node_id = node.id
        container.name = "{}_{}".format(container.image, uuid.uuid4())

        # set the weave IP immediately to prevent race condition
        # when containers are requested concurrently
        # container.weave_ip = addr
        # container.weave_prefixlen = prefixlen
        container.state = STATE_IN_PROGRESS

        db.persist(container, "containers")

        # log related setup
        container_log = ContainerLog.create_or_get(container)
        container_log.state = STATE_SETUP_IN_PROGRESS
        container_log.setup_log_url = url_for(
            "containerlog_setup",
            id=container_log.id,
            _external=True,
        )
        time.sleep(1)
        db.update(container_log.id, container_log, "container_logs")

        logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                               container_log.setup_log)

        # run the setup process
        helper_class = self.helper_classes[container_type]
        helper = helper_class(container, app, logpath)
        helper.setup()

        headers = {
            "X-Container-Setup-Log": container_log.setup_log_url,
            "Location": url_for("container", container_id=container.name),
        }
        return container.as_dict(), 202, headers


class ContainerLogResource(Resource):
    def get(self, id):
        container_log = db.get(id, "container_logs")
        if not container_log:
            return {"status": 404, "message": "Container log not found"}, 404
        return container_log.as_dict()

    def delete(self, id):
        container_log = db.get(id, "container_logs")
        if not container_log:
            return {"status": 404, "message": "Container log not found"}, 404

        db.delete(id, "container_logs")

        app = current_app._get_current_object()
        abs_setup_log = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                     container_log.setup_log)
        abs_teardown_log = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                        container_log.teardown_log)

        # cleanup unused logs
        for log in [abs_setup_log, abs_teardown_log]:
            try:
                os.unlink(log)
            except OSError:
                pass
        return {}, 204


class ContainerLogSetupResource(Resource):
    def get(self, id):
        container_log = db.get(id, "container_logs")
        if not container_log:
            return {"status": 404, "message": "Container setup log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                   container_log.setup_log)

        try:
            with open(abs_logpath) as fp:
                resp = container_log.as_dict()
                resp["setup_log_contents"] = [line.strip() for line in fp]
                return resp
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class ContainerLogTeardownResource(Resource):
    def get(self, id):
        container_log = db.get(id, "container_logs")
        if not container_log:
            return {"status": 404, "message": "Container teardown log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                   container_log.teardown_log)

        try:
            with open(abs_logpath) as fp:
                resp = container_log.as_dict()
                resp["teardown_log_contents"] = [line.strip() for line in fp]
                return resp
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class ContainerLogListResource(Resource):
    def get(self):
        container_logs = db.all("container_logs")
        return [container_log.as_dict() for container_log in container_logs]
