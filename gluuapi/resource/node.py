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
# from ..dockerclient import Docker
from ..database import db

# TODO: put it in config
NODE_TYPES = ('master', 'worker', 'discovery',)
DISCOVERY_PORT = '8500'
DISCOVERY_NODE_NAME = 'gluu.discovery'
#REMOTE_DOCKER_CERT_DIR = "/opt/gluu/docker/certs"
#CERT_FILES = ['ca.pem', 'cert.pem', 'key.pem']
# FSWATCHER_SCRIPT = "https://github.com/GluuFederation/cluster-tools/raw/master/fswatcher/fswatcher.py"
# FSWATCHER_CONF = "https://github.com/GluuFederation/cluster-tools/raw/master/fswatcher/fswatcher.conf"
RECOVERY_SCRIPT = "https://github.com/GluuFederation/cluster-tools/raw/master/recovery/recovery.py"
RECOVERY_CONF = "https://github.com/GluuFederation/cluster-tools/raw/master/recovery/recovery.conf"

class Discovery(object):
    pass

#TODO this is very ugly code now, next commit will be much better
class CreateNodeResource(Resource):
    def __init__(self):
        self.machine = Machine()

    def is_discovery_running(self):
        if db.count_from_table('nodes', db.where('type') == 'discovery'):
            return self.machine.status(DISCOVERY_NODE_NAME)
        return False

    def post(self, node_type):
        if node_type not in NODE_TYPES:
            return {
                "status": 404,
                "message": "Node type is not supported",
            }, 404

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
            discovery = db.search_from_table('nodes', db.where('type') == 'discovery')
            if not discovery:
                return {
                    "status": 404,
                    "message": "master node needs a discovery",
                }, 404

        if node_type == 'master':
            master = db.search_from_table('nodes', db.where('type') == 'master')
            if master:
                return {
                    "status": 404,
                    "message": "master node is already created",
                }, 404

        if node_type == 'worker':
            master = db.search_from_table('nodes', db.where('type') == 'master')
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

        data['type'] = node_type
        
        discovery = None
        if node_type != 'discovery':
            discovery = Discovery()
            discovery.ip = self.machine.ip(DISCOVERY_NODE_NAME)
            discovery.port = DISCOVERY_PORT

        if node_type == 'discovery':
            # try:
            #     #TODO make this hole thing side effect free and idempotent
            #     current_app.logger.info('creating discovery node')
            #     self.machine.create(node, provider, discovery)

            #     time.sleep(2)
            #     current_app.logger.info('installing consul')
            #     self.machine.ssh(node.name, 'sudo docker run -d --name=consul -p 8500:8500 -h consul --restart=always -v /opt/gluu/consul/data:/data progrium/consul -server -bootstrap')

            #     time.sleep(2)
            #     current_app.logger.info('saving node:{} to DB'.format(node.name))
            #     db.persist(node, 'nodes')
            # except RuntimeError as e:
            #     current_app.logger.warn(e)
            #     self.machine.rm(node.name)

            #     msg = str(e)
            #     return {
            #         "status": 500,
            #         "message": msg,
            #     }, 500

            #make discovery object
            node = DiscoveryNode(data)
            db.persist(node, 'nodes')
            ddn = DeployDiscoveryNode(node)
            ddn.deploy()

        if node_type == 'master':
            # try:
            #     #TODO make this hole thing side effect free and idempotent
            #     current_app.logger.info('creating {} node ({})'.format(node.name, node.type))
            #     self.machine.create(node, provider, discovery)

            #     time.sleep(2)
            #     #TODO if weaveinstall
            #     current_app.logger.info('installing weave')
            #     self.machine.ssh(node.name, 'sudo curl -L git.io/weave -o /usr/local/bin/weave')

            #     time.sleep(2)
            #     #TODO if weaveexec
            #     current_app.logger.info('adding exec permission of weave')
            #     self.machine.ssh(node.name, 'sudo chmod +x /usr/local/bin/weave')

            #     time.sleep(2)
            #     #TODO if weavelaunch
            #     current_app.logger.info('launching weave')
            #     self.machine.ssh(node.name, 'sudo weave launch')

            #     time.sleep(2)
            #     current_app.logger.info("retrieving registry certificate")
            #     self.machine.ssh(
            #         node.name,
            #         r"sudo mkdir -p /etc/docker/certs.d/{}".format(REGISTRY_BASE_URL),
            #     )
            #     registry_cert = get_registry_cert(
            #         os.path.join(current_app.config["REGISTRY_CERT_DIR"], "ca.crt")
            #     )
            #     self.machine.scp(
            #         registry_cert,
            #         r"{}:/etc/docker/certs.d/{}/ca.crt".format(
            #             node.name,
            #             REGISTRY_BASE_URL,
            #         ),
            #     )
            #     #pushing docker client cert
            #     current_app.logger.info("pushing docker client cert into master node")
            #     local_cert_path = os.path.join(os.getenv('HOME'), '.docker/machine/certs')
            #     self.machine.ssh(node.name, 'sudo mkdir -p {}'.format(REMOTE_DOCKER_CERT_DIR))
            #     for cf in CERT_FILES:
            #         self.machine.scp(
            #             os.path.join(local_cert_path, cf),
            #             "{}:{}".format(node.name, REMOTE_DOCKER_CERT_DIR),
            #         )

            #     # install fswatcher
            #     current_app.logger.info("installing fswatcher script in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /usr/bin".format(FSWATCHER_SCRIPT))
            #     self.machine.ssh(node.name, "sudo chmod +x /usr/bin/fswatcher.py")
            #     self.machine.ssh(node.name, "sudo apt-get -qq install -y --force-yes supervisor python-pip")
            #     self.machine.ssh(node.name, "sudo pip -q install --upgrade pip")
            #     self.machine.ssh(node.name, "sudo pip -q install virtualenv")
            #     self.machine.ssh(node.name, "sudo mkdir -p /root/.virtualenvs")
            #     self.machine.ssh(node.name, "sudo virtualenv /root/.virtualenvs/fswatcher")
            #     self.machine.ssh(node.name, "sudo /root/.virtualenvs/fswatcher/bin/pip -q install watchdog")

            #     # put fswatcher conf in /etc/supervisor/conf.d
            #     current_app.logger.info("configuring fswatcher daemon in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /etc/supervisor/conf.d".format(FSWATCHER_CONF))
            #     self.machine.ssh(node.name, "sudo supervisorctl reload")

            #     # install recovery
            #     current_app.logger.info("installing recovery script in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /usr/bin".format(RECOVERY_SCRIPT))
            #     self.machine.ssh(node.name, "sudo chmod +x /usr/bin/recovery.py")

            #     # put recovery conf in /etc/supervisor/conf.d
            #     current_app.logger.info("configuring recovery daemon in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /etc/supervisor/conf.d".format(RECOVERY_CONF))
            #     self.machine.ssh(node.name, "sudo supervisorctl reload")

            #     time.sleep(2)
            #     current_app.logger.info('saving node:{} to DB'.format(node.name))
            #     db.persist(node, 'nodes')
            # except RuntimeError as e:
            #     current_app.logger.warn(e)
            #     self.machine.rm(node.name)

            #     msg = str(e)
            #     return {
            #         "status": 500,
            #         "message": msg,
            #     }, 500

            node = MasterNode(data)
            db.persist(node, 'nodes')
            dmn = DeployMasterNode(node, discovery, current_app._get_current_object())
            dmn.deploy()

        if node_type == 'worker':
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

            # try:
            #     #TODO make this hole thing side effect free and idempotent
            #     current_app.logger.info('creating {} node ({})'.format(node.name, node.type))
            #     self.machine.create(node, provider, discovery)

            #     time.sleep(2)
            #     #TODO if weaveinstall
            #     current_app.logger.info('installing weave')
            #     self.machine.ssh(node.name, 'sudo curl -L git.io/weave -o /usr/local/bin/weave')

            #     time.sleep(2)
            #     #TODO if weaveexec
            #     current_app.logger.info('adding exec permission of weave')
            #     self.machine.ssh(node.name, 'sudo chmod +x /usr/local/bin/weave')

            #     time.sleep(2)
            #     master = db.search_from_table('nodes', db.where('type') == 'master')[0]
            #     ip = self.machine.ip(master.name)
            #     current_app.logger.info('launching weave')
            #     self.machine.ssh(node.name, 'sudo weave launch {}'.format(ip))

            #     time.sleep(2)
            #     current_app.logger.info("retrieving registry certificate")
            #     self.machine.ssh(
            #         node.name,
            #         r"sudo mkdir -p /etc/docker/certs.d/{}".format(REGISTRY_BASE_URL),
            #     )
            #     registry_cert = get_registry_cert(
            #         os.path.join(current_app.config["REGISTRY_CERT_DIR"], "ca.crt")
            #     )
            #     self.machine.scp(
            #         registry_cert,
            #         r"{}:/etc/docker/certs.d/{}/ca.crt".format(
            #             node.name,
            #             REGISTRY_BASE_URL,
            #         ),
            #     )

            #     # install recovery
            #     current_app.logger.info("installing recovery script in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /usr/bin".format(RECOVERY_SCRIPT))
            #     self.machine.ssh(node.name, "sudo chmod +x /usr/bin/recovery.py")
            #     self.machine.ssh(node.name, "sudo apt-get -qq install -y --force-yes supervisor")

            #     # put recovery conf in /etc/supervisor/conf.d
            #     current_app.logger.info("configuring recovery daemon in {} node".format(node.name))
            #     self.machine.ssh(node.name, "sudo wget {} -P /etc/supervisor/conf.d".format(RECOVERY_CONF))
            #     self.machine.ssh(node.name, "sudo supervisorctl reload")

            #     time.sleep(2)
            #     current_app.logger.info('saving node:{} to DB'.format(node.name))
            #     db.persist(node, 'nodes')
            # except RuntimeError as e:
            #     current_app.logger.warn(e)
            #     self.machine.rm(node.name)

            #     msg = str(e)
            #     return {
            #         "status": 500,
            #         "message": msg,
            #     }, 500
            node = WorkerNode(data)
            db.persist(node, 'nodes')
            dwn = DeployWorkerNode(node, discovery, current_app._get_current_object())
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
        nodes = db.search_from_table('nodes', db.where('name') == node_name)
        if not nodes:
            return {"status": 404, "message": "node not found"}, 404
        else:
            return nodes[0].as_dict()

    # here node_id is name TODO: this is about to change to node_name
    def delete(self, node_name):
        nodes = db.search_from_table('nodes', db.where('name') == node_name)
        if nodes:
            node = nodes[0]
        else:
            return {
                "status": 404,
                "message": "node not found"
            }, 404

        if node.type == 'master' and db.count_from_table('nodes', db.where('type') == 'worker'):
            return {
                "status": 404,
                "message": "there are still worker nodes running"
            }, 404

        if node.type == 'discovery' and db.count_from_table('nodes', db.where('type') == 'master'):
            return {
                "status": 404,
                "message": "master node still running"
            }, 404

        try:
            #TODO: if machine.search is true then remove it otherewise only remove from db
            self.machine.rm(node.name)
            db.delete(node.id, 'nodes')
        except RuntimeError as e:
            current_app.logger.warn(e)
            msg = str(e)  # TODO log
            return {
                "status": 500,
                "message": msg,
            }, 500
        return {}, 204

    def put(self, node_name):
        pass
