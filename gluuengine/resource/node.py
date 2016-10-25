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
from ..node import DeployDiscoveryNode
from ..node import DeployMasterNode
from ..node import DeployWorkerNode
from ..machine import Machine
from ..database import db
from ..utils import as_boolean

# TODO: put it in config
NODE_TYPES = ('master', 'worker', 'discovery',)
DISCOVERY_PORT = '8500'
DISCOVERY_NODE_NAME = 'gluu.discovery'


class Discovery(object):
    pass


#TODO this is very ugly code now
class CreateNodeResource(Resource):
    def __init__(self):
        self.machine = Machine()

    def is_discovery_running(self):
        if db.count_from_table('nodes', {'type': 'discovery'}):
            return self.machine.status(DISCOVERY_NODE_NAME)
        return False

    def post(self, node_type):
        app = current_app._get_current_object()

        if node_type not in NODE_TYPES:
            return {
                "status": 404,
                "message": "Node type is not supported",
            }, 404
        #TODO: need to remove this name constrain
        if node_type == 'discovery' and request.form.get('name', '') != DISCOVERY_NODE_NAME:
            return {
                "status": 404,
                "message": "discovery node name must be, " + DISCOVERY_NODE_NAME,
            }, 404

        if node_type == 'discovery' and self.is_discovery_running():
            return {
                "status": 404,
                "message": "discovery server is already created",
            }, 404

        if node_type == 'master':
            discovery = db.search_from_table('nodes', {'type': 'discovery'})
            if not discovery:
                return {
                    "status": 404,
                    "message": "master node needs a discovery",
                }, 404

        if node_type == 'master':
            master = db.search_from_table('nodes', {'type': 'master'})
            if master:
                return {
                    "status": 404,
                    "message": "master node is already created",
                }, 404

        if node_type == 'worker':
            master = db.search_from_table('nodes', {'type': 'master'})
            if not master:
                return {
                    "status": 404,
                    "message": "worker node needs a master",
                }, 404

        data, errors = NodeReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        #TODO: get discovery node name
        discovery = None
        if node_type != 'discovery':
            discovery = Discovery()
            discovery.ip = self.machine.ip(DISCOVERY_NODE_NAME)
            discovery.port = DISCOVERY_PORT

        if node_type == 'discovery':
            node = DiscoveryNode(data)
            db.persist(node, 'nodes')
            ddn = DeployDiscoveryNode(node, app)
            ddn.deploy()

        if node_type == 'master':
            node = MasterNode(data)
            db.persist(node, 'nodes')
            dmn = DeployMasterNode(node, discovery, app)
            dmn.deploy()

        if node_type == 'worker':
            if as_boolean(app.config["ENABLE_LICENSE"]):
                try:
                    license_key = db.all("license_keys")[0]
                except IndexError:
                    license_key = None

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

            node = WorkerNode(data)
            db.persist(node, 'nodes')
            dwn = DeployWorkerNode(node, discovery, app)
            dwn.deploy()

        headers = {
            "Location": url_for("node", node_name=node.name),
        }
        return node.as_dict(), 202, headers


class NodeListResource(Resource):
    def get(self):
        nodes = db.all("nodes")
        return [node.as_dict() for node in nodes]


class NodeResource(Resource):
    def __init__(self):
        self.machine = Machine()

    def get(self, node_name):
        nodes = db.search_from_table('nodes', {'name': node_name})
        if not nodes:
            return {"status": 404, "message": "node not found"}, 404
        else:
            return nodes[0].as_dict()

    def delete(self, node_name):
        nodes = db.search_from_table('nodes', {'name': node_name})
        if nodes:
            node = nodes[0]
        else:
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

        if node.type == 'master' and db.count_from_table('nodes', {'type': 'worker'}):
            return {
                "status": 403,
                "message": "there are still worker nodes running"
            }, 403

        if node.type == 'discovery' and db.count_from_table('nodes', {'type': 'master'}):
            return {
                "status": 403,
                "message": "master node still running"
            }, 403

        running = self.machine.is_running(node.name)
        if running:
            try:
                self.machine.rm(node.name)
                db.delete(node.id, 'nodes')
            except RuntimeError as e:
                current_app.logger.warn(e)
                msg = str(e)  # TODO log
                return {
                    "status": 500,
                    "message": msg,
                }, 500
        else:
            db.delete(node.id, 'nodes')
        return {}, 204

    def put(self, node_name):
        nodes = db.search_from_table('nodes', {'name': node_name})
        if nodes:
            node = nodes[0]
        else:
            return {
                "status": 404,
                "message": "node not found"
            }, 404

        discovery = None
        if node.type != 'discovery':
            discovery = Discovery()
            discovery.ip = self.machine.ip(DISCOVERY_NODE_NAME)
            discovery.port = DISCOVERY_PORT

        if node.type == 'discovery':
            dn = DeployDiscoveryNode(node, current_app._get_current_object())
        if node.type == 'master':
            dn = DeployMasterNode(node, discovery, current_app._get_current_object())
        if node.type == 'worker':
            dn = DeployWorkerNode(node, discovery, current_app._get_current_object())

        dn.deploy()
        headers = {
            "Location": url_for("node", node_name=node.name),
        }
        return node.as_dict(), 202, headers
