# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource

from ..reqparser import NodeReq
from ..model import DiscoveryNode
from ..model import MasterNode
from ..model import WorkerNode
from ..model import MsgconNode
from ..model import Node
from ..model import LicenseKey
from ..node import DeployDiscoveryNode
from ..node import DeployMasterNode
from ..node import DeployWorkerNode
from ..node import DeployMsgconNode
from ..machine import Machine
from ..extensions import db
from ..utils import as_boolean

# TODO: put it in config
NODE_TYPES = ('master', 'worker', 'discovery', 'msgcon')
DISCOVERY_PORT = '8500'


class Discovery(object):
    pass


def find_discovery():
    return Node.query.filter_by(type="discovery").first()


def load_discovery(machine):
    dnode = find_discovery()
    discovery = Discovery()
    discovery.ip = machine.ip(dnode.name)
    discovery.port = DISCOVERY_PORT
    return discovery


class CreateNodeResource(Resource):
    def __init__(self):
        self.machine = Machine()

    def post(self, node_type):
        app = current_app._get_current_object()

        if node_type not in NODE_TYPES:
            return {
                "status": 404,
                "message": "Node type is not supported",
            }, 404

        data, errors = NodeReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        if node_type == 'discovery':
            if Node.query.filter_by(type="discovery").count():
                return {
                    "status": 403,
                    "message": "discovery node is already created",
                }, 403

            node = DiscoveryNode(**data)
            db.session.add(node)
            db.session.commit()
            dn = DeployDiscoveryNode(node, app)
            dn.deploy()

        if node_type == 'msgcon':
            if not Node.query.filter_by(type="master").count():
                return {
                    "status": 403,
                    "message": "msgcon node needs a master node",
                }, 403
            discovery = load_discovery(self.machine)
            node = MsgconNode(**data)
            db.session.add(node)
            db.session.commit()
            dn = DeployMsgconNode(node, discovery, app)
            dn.deploy()

        if node_type == 'master':
            if not Node.query.filter_by(type="discovery").count():
                return {
                    "status": 403,
                    "message": "master node needs a discovery",
                }, 403

            if Node.query.filter_by(type="master").count():
                return {
                    "status": 403,
                    "message": "master node is already created",
                }, 403
            discovery = load_discovery(self.machine)
            node = MasterNode(**data)
            db.session.add(node)
            db.session.commit()
            dn = DeployMasterNode(node, discovery, app)
            dn.deploy()

        if node_type == 'worker':
            if not Node.query.filter_by(type="master").count():
                return {
                    "status": 403,
                    "message": "worker node needs a master node",
                }, 403

            if as_boolean(app.config["ENABLE_LICENSE"]):
                license_key = LicenseKey.query.first()

                if not license_key:
                    return {
                        "status": 403,
                        "message": "creating worker node requires a license key",
                    }, 403

                # we have license key, but it's expired
                if license_key.expired:
                    return {
                        "status": 403,
                        "message": "creating worker node requires a non-expired license key",
                    }, 403

                # we have license key, but it's for another type of product
                if license_key.mismatched:
                    return {
                        "status": 403,
                        "message": "creating worker node requires a DE product license key",
                    }, 403

                if not license_key.is_active:
                    return {
                        "status": 403,
                        "message": "creating worker node requires active license",
                    }, 403
            discovery = load_discovery(self.machine)
            node = WorkerNode(**data)
            db.session.add(node)
            db.session.commit()
            dn = DeployWorkerNode(node, discovery, app)
            dn.deploy()

        headers = {
            "Location": url_for("node", node_name=node.name),
        }
        return node.as_dict(), 202, headers


class NodeListResource(Resource):
    def get(self):
        return [node.as_dict() for node in Node.query]


class NodeResource(Resource):
    def __init__(self):
        self.machine = Machine()

    def get(self, node_name):
        node = Node.query.filter_by(name=node_name).first()
        if not node:
            return {"status": 404, "message": "node not found"}, 404
        return node.as_dict()

    def delete(self, node_name):
        node = Node.query.filter_by(name=node_name).first()
        if not node:
            return {
                "status": 404,
                "message": "node not found"
            }, 404

        # reject request if node has containers
        if node.count_containers():
            return {
                "status": 403,
                "message": "cannot delete node when it has containers",
            }, 403

        if node.type == 'master' and Node.query.filter_by(type="worker").count():
            return {
                "status": 403,
                "message": "there are still worker nodes running"
            }, 403

        if node.type == 'discovery' and Node.query.filter_by(type="master").count():
            return {
                "status": 403,
                "message": "master node still running"
            }, 403

        running = self.machine.is_running(node.name)
        if running:
            try:
                self.machine.rm(node.name)
                db.session.delete(node)
                db.session.commit()
            except RuntimeError as e:
                current_app.logger.warn(e)
                msg = str(e)  # TODO log
                return {
                    "status": 500,
                    "message": msg,
                }, 500
                db.session.rollback()
        else:
            db.session.delete(node)
            db.session.commit()
        return {}, 204

    def put(self, node_name):
        app = current_app._get_current_object()

        node = Node.query.filter_by(name=node_name).first()
        if not node:
            return {
                "status": 404,
                "message": "node not found"
            }, 404

        dcv_node = find_discovery()

        if node.type != 'discovery':
            discovery = Discovery()
            discovery.ip = self.machine.ip(dcv_node.name)
            discovery.port = DISCOVERY_PORT

        if node.type == 'discovery':
            dn = DeployDiscoveryNode(node, app)
        if node.type == 'master':
            dn = DeployMasterNode(node, discovery, app)
        if node.type == 'worker':
            dn = DeployWorkerNode(node, discovery, app)
        if node.type == "msgcon":
            dn = DeployMsgconNode(node, discovery, app)

        dn.deploy()
        headers = {
            "Location": url_for("node", node_name=node.name),
        }
        return node.as_dict(), 202, headers
