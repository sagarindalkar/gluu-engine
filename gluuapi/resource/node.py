# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import uuid

#from flask import current_app as app
from flask import request
from flask import url_for
from flask_restful import Resource

from ..reqparser import NodeReq
from ..model import Node
from ..machine import Machine
from ..dockerclient import Docker
from ..database import db

NODE_TYPES = ['master', 'worker', 'kv'] #TODO: put it in config

class CreateNodeResource(Resource):
    def is_kv_running(self):
        if db.count_from_table('nodes', db.where('type') == 'kv'):
            m = Machine()
            return m.status('gluu.discovery')
        return False

    def post(self, node_type):
        if node_type not in NODE_TYPES:
            return {
                "status": 404,
                "message": "Node type is not supported"
            }, 404

        if node_type == 'kv' and request.form.get('name','') != 'gluu.discovery':
            return {
                "status": 404,
                "message": "kv node name must be, gluu.discovery"
            }, 404

        if node_type == 'kv' and self.is_kv_running():
            return {
                "status": 404,
                "message": "discovery server is already created"
            }, 404

        data, errors = NodeReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        data['type'] = node_type

        #create node
        m = Machine()
        node = Node(data)
        provider = db.get(data['provider_id'], 'digitalocean_providers')

        discovery = None
        if data['type'] != 'kv':
            class Discovery(object):
                pass
            discovery = Discovery()
            discovery.ip = m.ip('gluu.discovery')
            discovery.port = '8500'

        m.create(node, provider, discovery)
        db.persist(node, 'nodes')

        if node.type == 'kv':
            conf = m.config(node.name)
            docker = Docker(conf)
            #TODO install consul
        if node.type in ['master', 'worker']:
            #TODO install weave
            m.ssh(node.name, 'sudo curl -L git.io/weave -o /usr/local/bin/weave')
            m.ssh(node.name, 'sudo chmod +x /usr/local/bin/weave')

        headers = {
            "Location": url_for("node", node_id=node.id),
        }
        return node.as_dict(), 201, headers


class NodeListResource(Resource):
    def get(self):
        nodes = db.all("nodes")
        return [node.as_dict() for node in nodes]

class NodeResource(Resource):
    def get(self, node_id):
        node = db.get(node_id, 'nodes')
        if not node:
            return {"status": 404, "message": "Provider not found"}, 404
        return node.as_dict()
