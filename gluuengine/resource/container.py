# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
from itertools import cycle

import concurrent.futures
from flask import abort
from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource
from crochet import run_in_reactor

from ..extensions import db
from ..reqparser import ContainerReq
from ..model import STATE_SUCCESS
from ..model import STATE_IN_PROGRESS
from ..model import STATE_SETUP_IN_PROGRESS
from ..model import STATE_TEARDOWN_IN_PROGRESS
from ..helper import OxauthContainerHelper
from ..helper import OxtrustContainerHelper
# from ..helper import OxidpContainerHelper
from ..helper import NginxContainerHelper
# from ..helper import OxasimbaContainerHelper
from ..helper import OxelevenContainerHelper
from ..model import OxauthContainer
from ..model import OxtrustContainer
from ..model.container import Container
# from ..model import OxidpContainer
from ..model import NginxContainer
# from ..model import OxasimbaContainer
from ..model import ContainerLog
from ..model import OxelevenContainer
from ..machine import Machine
from ..utils import as_boolean
from ..model.node import Node
from ..model import Cluster


#: List of supported container
CONTAINER_CHOICES = (
    "oxauth",
    "oxtrust",
    # "oxidp",  # disabled for now
    "nginx",
    # "oxasimba",  # disabled for now
    "oxeleven",
)


def get_container(db, container_id):
    return Container.query.filter(db.or_(
        Container.id == container_id, Container.name == container_id,
    )).first()


def target_node_reachable(node_name):
    return Machine().status(node_name)


def master_node_reachable():
    node = Node.query.filter_by(type="master").first()
    if not node:
        return False
    return Machine().status(node.name)


def discovery_node_reachable():
    node = Node.query.filter_by(type="discovery").first()
    if not node:
        return False
    return Machine().status(node.name)


def get_containerlog(db, containerlog_name):
    return ContainerLog.query.filter_by(container_name=containerlog_name).first()


class ContainerResource(Resource):
    helper_classes = {
        "oxauth": OxauthContainerHelper,
        "oxtrust": OxtrustContainerHelper,
        # "oxidp": OxidpContainerHelper,  # disabled for now
        "nginx": NginxContainerHelper,
        # "oxasimba": OxasimbaContainerHelper,
        "oxeleven": OxelevenContainerHelper,
    }

    def get(self, container_id):
        container = get_container(db, container_id)

        if not container:
            return {"status": 404, "message": "Container not found"}, 404
        return container.as_dict()

    def delete(self, container_id):
        app = current_app._get_current_object()
        force_delete = as_boolean(request.args.get("force_rm", False))

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

        node = Node.query.get(container.node_id)

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
        db.session.delete(container)
        db.session.commit()

        container_log = ContainerLog.create_or_get(container)
        container_log.state = STATE_TEARDOWN_IN_PROGRESS
        # TODO: update the row
        db.session.add(container_log)
        db.session.commit()
        logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                               container_log.teardown_log)

        # run the teardown process
        helper_class = self.helper_classes[container.type]
        helper = helper_class(container, app, logpath)
        helper.teardown()

        headers = {
            "X-Container-Teardown-Log": url_for(
                "containerlog_teardown",
                container_name=container_log.container_name,
                _external=True,
            ),
        }
        return {}, 204, headers


class ContainerListResource(Resource):
    def get(self, container_type=""):
        if not container_type:
            return [
                container.as_dict()
                for container in Container.query
                                          .order_by(Container.created_at.asc())
            ]

        if container_type not in CONTAINER_CHOICES:
            abort(404)

        return [
            container.as_dict()
            for container in Container.query
                                      .filter_by(type=container_type)
                                      .order_by(Container.created_at.asc())
        ]


class NewContainerResource(Resource):
    helper_classes = {
        "oxauth": OxauthContainerHelper,
        "oxtrust": OxtrustContainerHelper,
        # "oxidp": OxidpContainerHelper,  # disabled for now
        "nginx": NginxContainerHelper,
        # "oxasimba": OxasimbaContainerHelper,
        "oxeleven": OxelevenContainerHelper,
    }

    container_classes = {
        "oxauth": OxauthContainer,
        "oxtrust": OxtrustContainer,
        # "oxidp": OxidpContainer,  # disabled for now
        "nginx": NginxContainer,
        # "oxasimba": OxasimbaContainer,
        "oxeleven": OxelevenContainer,
    }

    def post(self, container_type):
        app = current_app._get_current_object()

        if container_type not in CONTAINER_CHOICES:
            abort(404)

        data, errors = ContainerReq(
            context={
                "enable_license": as_boolean(app.config["ENABLE_LICENSE"]),
            },
        ).load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid params",
                "params": errors,
            }, 400

        cluster = Cluster.query.first()
        if not cluster:
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

        trust_or_oxeleven = (container_type in ('oxtrust', 'oxeleven'))

        # only allow one oxtrust and one oxeleven per cluster
        if trust_or_oxeleven and cluster.count_containers(type_=container_type):
            return {
                "status": 403,
                "message": "cannot deploy additional {} container to cluster".format(container_type),
            }, 403

        # oxtrust and oxeleven only deploy in master node
        if trust_or_oxeleven and node.type != "master":
            return {
                "status": 403,
                "message": "cannot deploy {} container to non-master node".format(container_type),
            }, 403

        # only allow 1 nginx per node
        if container_type == "nginx" and node.count_containers(type_="nginx"):
            return {
                "status": 403,
                "message": "cannot deploy additional nginx container "
                           "to specified node",
            }, 403

        # pre-populate the container object
        container_class = self.container_classes[container_type]
        container = container_class(**{
            "cluster_id": cluster.id,
            "node_id": node.id,
            "state": STATE_IN_PROGRESS,
            # "container_attrs": data["container_attrs"],
        })
        db.session.add(container)
        db.session.flush()
        container.name = "{}_{}".format(container.image, container.id)
        db.session.commit()

        # log related setup
        container_log = ContainerLog.create_or_get(container)
        container_log.state = STATE_SETUP_IN_PROGRESS
        # TODO: update the row
        db.session.add(container_log)
        db.session.commit()
        logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                               container_log.setup_log)

        # run the setup process
        helper_class = self.helper_classes[container_type]
        helper = helper_class(container, app, logpath)
        helper.setup()

        headers = {
            "X-Container-Setup-Log": url_for(
                "containerlog_setup",
                container_name=container.name,
                _external=True,
            ),
            "Location": url_for("container", container_id=container.name),
        }
        return container.as_dict(), 202, headers


def format_container_log_response(container_log):
    app = current_app._get_current_object()

    setup_log = os.path.join(app.config["CONTAINER_LOG_DIR"],
                             container_log.setup_log)
    teardown_log = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                container_log.teardown_log)

    resp = container_log.as_dict()

    resp["setup_log_url"] = ""
    if os.path.exists(setup_log):
        resp["setup_log_url"] = url_for(
            "containerlog_setup",
            container_name=container_log.container_name,
            _external=True,
        )

    resp["teardown_log_url"] = ""
    if os.path.exists(teardown_log):
        resp["teardown_log_url"] = url_for(
            "containerlog_teardown",
            container_name=container_log.container_name,
            _external=True,
        )
    return resp


class ContainerLogResource(Resource):
    def get(self, container_name):
        container_log = get_containerlog(db, container_name)
        if not container_log:
            return {"status": 404, "message": "Container log not found"}, 404
        return format_container_log_response(container_log)

    def delete(self, container_name):
        container_log = get_containerlog(db, container_name)
        if not container_log:
            return {"status": 404, "message": "Container log not found"}, 404

        db.session.delete(container_log)
        db.session.commit()

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
    def get(self, container_name):
        container_log = get_containerlog(db, container_name)
        if not container_log:
            return {"status": 404, "message": "Container setup log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                   container_log.setup_log)

        try:
            with open(abs_logpath) as fp:
                resp = format_container_log_response(container_log)
                resp["setup_log_contents"] = [line.strip() for line in fp]
                return resp
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class ContainerLogTeardownResource(Resource):
    def get(self, container_name):
        container_log = get_containerlog(db, container_name)
        if not container_log:
            return {"status": 404, "message": "Container teardown log not found"}, 404

        app = current_app._get_current_object()
        abs_logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                   container_log.teardown_log)

        try:
            with open(abs_logpath) as fp:
                resp = format_container_log_response(container_log)
                resp["teardown_log_contents"] = [line.strip() for line in fp]
                return resp
        except IOError:
            return {
                "status": 404,
                "message": "log not found",
            }, 404


class ContainerLogListResource(Resource):
    def get(self):
        return [
            format_container_log_response(container_log)
            for container_log in ContainerLog.query
                                             .order_by(ContainerLog.created_at.asc())
        ]


class ScaleContainerResource(Resource):
    SCALE_ENABLE_CONTAINERS = (
        "oxauth",
        # "oxidp",  # disabled for now
    )

    helper_classes = {
        "oxauth": OxauthContainerHelper,
        # "oxidp": OxidpContainerHelper,  # disabled for now
    }

    container_classes = {
        "oxauth": OxauthContainer,
        # "oxidp": OxidpContainer,  # disabled for now
    }

    def get_running_nodes(self):
        m = Machine()
        running_nodes = m.list('running')

        try:
            dcv_node = Node.query.filter_by(type="discovery").first()
            running_nodes.remove(dcv_node.name)
        except IndexError:
            pass
        return running_nodes

    def make_node_id_pool(self, nodes):
        running_nodes = self.get_running_nodes()
        running_nodes_ids = [node.id for node in nodes if node.name in running_nodes]
        #make a circular id list of running nodes
        return cycle(running_nodes_ids)

    def setup_obj_generator(self, app, container_type, number, cluster_id, node_id_pool):
        with app.app_context():
            for i in xrange(number):
                container_class = self.container_classes[container_type]
                container = container_class(**{
                    "cluster_id": cluster_id,
                    "node_id": node_id_pool.next(),
                    "state": STATE_IN_PROGRESS,
                    # "container_attrs": {},
                })
                db.session.add(container)
                db.session.flush()
                container.name = "{}_{}".format(container.image, container.id)
                db.session.commit()

                # log related setup
                container_log = ContainerLog.create_or_get(container)
                container_log.state = STATE_SETUP_IN_PROGRESS
                # TODO: update the row
                db.session.add(container_log)
                db.session.commit()
                logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                       container_log.setup_log)

                # make the setup obj
                helper_class = self.helper_classes[container_type]
                helper = helper_class(container, app, logpath)
                yield helper

    @run_in_reactor
    def scaleosorus(self, setup_obj_generator):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for setup_obj in setup_obj_generator:
                executor.submit(setup_obj.mp_setup)

    def post(self, container_type, number):
        app = current_app._get_current_object()
        #validate container type
        if container_type not in self.SCALE_ENABLE_CONTAINERS:
            abort(404)

        if number <= 0:
            return {
                "status": 403,
                "message": "cannot deploy 0 or lower number of container",
            }, 403

        cluster = Cluster.query.first()
        if not cluster:
            return {
                "status": 403,
                "message": "container deployment requires a cluster",
            }, 403

        # get id list of running nodes
        nodes = Node.query.filter(Node.type.in_(["master", "worker"])).all()
        if not nodes:
            return {
                "status": 403,
                "message": "container deployment requires nodes",
            }, 403

        node_id_pool = self.make_node_id_pool(nodes)

        #make a list of container setup object
        sg = self.setup_obj_generator(app, container_type, number, cluster.id, node_id_pool)

        self.scaleosorus(sg)

        return {
            "status": 202,
            "message": 'deploying {} {}'.format(number, container_type),
        }, 202

    @run_in_reactor
    def delscaleosorus(self, delete_obj_generator):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for delete_obj in delete_obj_generator:
                executor.submit(delete_obj.mp_teardown)

    def delete_obj_generator(self, app, containers):
        with app.app_context():
            for container in containers:
                db.session.delete(container)
                db.session.commit()
                container_log = ContainerLog.create_or_get(container)
                container_log.state = STATE_TEARDOWN_IN_PROGRESS
                # TODO: update the row
                db.session.add(container_log)
                db.session.commit()
                logpath = os.path.join(app.config["CONTAINER_LOG_DIR"],
                                       container_log.teardown_log)
                helper_class = self.helper_classes[container.type]
                helper = helper_class(container, app, logpath)
                yield helper

    def delete(self, container_type, number):
        app = current_app._get_current_object()

        #validate container type
        if container_type not in self.SCALE_ENABLE_CONTAINERS:
            abort(404)

        #validate number
        if number <= 0:
            return {
                "status": 403,
                "message": "cannot deploy 0 or lower number of container",
            }, 403

        # get the count of requested container type
        counter = Container.query.filter_by(
            type=container_type, state=STATE_SUCCESS,
        ).count()
        if number > counter:
            return {
                "status": 403,
                "message": "delete request number is greater than running containers",
            }, 403

        # get the list of container object
        containers = Container.query.filter_by(
            type=container_type, state=STATE_SUCCESS,
        ).all()

        # select and arrange containers
        nodes = Node.query.filter(Node.type.in_(["master", "worker"])).all()
        node_id_pool = self.make_node_id_pool(nodes)

        containers_reorder = []
        while True:
            nid = node_id_pool.next()
            for con in containers:
                if con.node_id == nid and con not in containers_reorder:
                    containers_reorder.append(con)
                    break
            if len(containers_reorder) == number:
                break

        # get a genatator of delete_object
        dg = self.delete_obj_generator(app, containers_reorder)
        # start backgroung delete operation
        self.delscaleosorus(dg)

        return {
            "status": 202,
            "message": 'deleting {} {}'.format(number, container_type),
        }, 202
