# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

# import os
import time
from crochet import run_in_reactor

from ..database import db
from ..machine import Machine
from ..log import create_file_logger
from ..model import Provider
from sqlalchemy.orm.attributes import flag_modified
from ..model import Node

# REMOTE_DOCKER_CERT_DIR = "/opt/gluu/docker/certs"
# CERT_FILES = ['ca.pem', 'cert.pem', 'key.pem']


class DeployNode(object):
    def __init__(self, node_model_obj, app):
        self.app = app
        self.node_id = node_model_obj.id
        self.logger = create_file_logger(app.config['NODE_LOG_PATH'], name=node_model_obj.name)
        self.machine = Machine()

        with self.app.app_context():
            self.provider = Provider.query.get(node_model_obj.provider_id)

    def _rng_tools(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if node.state_attrs["state_rng_tools"]:
                return

            try:
                self.logger.info("installing rng-tools in {} node".format(node.name))
                cmd_list = [
                    "sudo wget {} -O /etc/default/rng-tools".format(self.app.config["RNG_TOOLS_CONF_URL"]),
                    """sudo apt-get -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" install -y rng-tools""",
                ]
                self.machine.ssh(node.name, ' && '.join(cmd_list))
                node.state_attrs["state_rng_tools"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to install rng-tools')
                self.logger.error(e)

    def _pull_images(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if node.state_attrs["state_pull_images"]:
                return

            try:
                self.logger.info("pulling gluu images in {} node".format(node.name))
                cmd_list = [
                    'sudo docker pull gluufederation/oxauth:{}'.format(self.app.config["GLUU_IMAGE_TAG"]),
                    'sudo docker pull gluufederation/nginx:{}'.format(self.app.config["GLUU_IMAGE_TAG"]),
                ]
                self.machine.ssh(node.name, ' && '.join(cmd_list))
                node.state_attrs["state_pull_images"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to pull images')
                self.logger.error(e)


class DeployDiscoveryNode(DeployNode):
    def __init__(self, node_model_obj, app):
        super(DeployDiscoveryNode, self).__init__(node_model_obj, app)

    @run_in_reactor
    def deploy(self):
        self._node_create()
        self._install_consul()
        self._is_completed()

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def _node_create(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if node.state_attrs["state_node_create"]:
                return

            try:
                self.logger.info('creating discovery node')
                self.machine.create(node, self.provider, None)
                node.state_attrs["state_node_create"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to create node')
                self.logger.error(e)
            finally:
                time.sleep(1)

    def _install_consul(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            # do nothing if node has not created yet
            if not node.state_attrs["state_node_create"]:
                return

            # do nothing if consul already installed
            if node.state_attrs["state_install_consul"]:
                return

            self.logger.info('installing consul')
            try:
                self.machine.ssh(
                    node.name,
                    " ".join([
                        "sudo docker run -d ",
                        "--name=consul -p 8500:8500 -h consul --restart=always",
                        "-v /opt/gluu/consul/data:/data progrium/consul",
                        "-server -bootstrap"
                    ])
                )
                node.state_attrs["state_install_consul"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to install consul')
                self.logger.error(e)
            finally:
                time.sleep(1)

    def _is_completed(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)
            if all([node.state_attrs["state_node_create"],
                    node.state_attrs["state_install_consul"]]):
                node.state_attrs["state_complete"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
                self.logger.info('node deployment is done')


class DeployMasterNode(DeployNode):
    def __init__(self, node_model_obj, discovery, app):
        super(DeployMasterNode, self).__init__(node_model_obj, app)
        self.discovery = discovery

    @run_in_reactor
    def deploy(self):
        self._node_create()
        self._network_create()
        self._rng_tools()
        self._pull_images()
        self._is_completed()

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def _is_completed(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)
            if all([node.state_attrs["state_node_create"],
                    node.state_attrs["state_network_create"],
                    node.state_attrs["state_rng_tools"],
                    node.state_attrs["state_pull_images"]]):
                node.state_attrs["state_complete"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
                self.logger.info('node deployment is done')

    def _node_create(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            # do nothing if node has been created
            if node.state_attrs["state_node_create"]:
                return

            try:
                self.logger.info('creating {} node ({})'.format(node.name, node.type))
                self.machine.create(node, self.provider, self.discovery)
                node.state_attrs["state_node_create"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to create node')
                self.logger.error(e)

    # #pushing docker cert so that fswatcher script can work
    # def _docker_cert(self):
    #     node = Node.query.get(self.node_id)
    #     if not node.state_attrs["state_node_create"]:
    #         return

    #     if node.state_attrs["state_docker_cert"]:
    #         return

    #     try:
    #         self.logger.info("pushing docker client cert into master node")
    #         local_cert_path = os.path.join(os.getenv('HOME'), '.docker/machine/certs')
    #         self.machine.ssh(node.name, 'sudo mkdir -p {}'.format(REMOTE_DOCKER_CERT_DIR))
    #         for cf in CERT_FILES:
    #             self.machine.scp(
    #                 os.path.join(local_cert_path, cf),
    #                 "{}:{}".format(node.name, REMOTE_DOCKER_CERT_DIR),
    #             )
    #         node.state_attrs["state_docker_cert"] = True
    #         flag_modified(node, "state_attrs")
    #         db.session.commit()
    #     except RuntimeError as e:
    #         db.session.rollback()
    #         self.logger.error('failed to push docker client cert into master node')
    #         self.logger.error(e)

    # def _fswatcher(self):
    #     node = Node.query.get(self.node_id)

    #     if not node.state_attrs["state_node_create"]:
    #         return

    #     if node.state_attrs["state_fswatcher"]:
    #         return

    #     try:
    #         self.logger.info("installing fswatcher in {} node".format(node.name))
    #         cmd_list = [
    #             "sudo wget {} -P /usr/bin".format(self.app.config["FSWATCHER_SCRIPT_URL"]),
    #             "sudo chmod +x /usr/bin/fswatcher.py",
    #             "sudo apt-get -qq install -y --force-yes supervisor python-pip",
    #             "sudo pip -q install --upgrade pip",
    #             "sudo pip -q install virtualenv",
    #             "sudo mkdir -p /root/.virtualenvs",
    #             "sudo virtualenv /root/.virtualenvs/fswatcher",
    #             "sudo /root/.virtualenvs/fswatcher/bin/pip -q install watchdog",
    #             "sudo wget {} -P /etc/supervisor/conf.d".format(self.app.config["FSWATCHER_CONF_URL"]),
    #             "sudo supervisorctl reload",
    #         ]
    #         self.machine.ssh(node.name, ' && '.join(cmd_list))
    #         node.state_attrs["state_fswatcher"] = True
    #         flag_modified(node, "state_attrs")
    #         db.session.commit()
    #     except RuntimeError as e:
    #         db.session.rollback()
    #         self.logger.error('failed to install fswatcher script')
    #         self.logger.error(e)

    def _network_create(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if node.state_attrs["state_network_create"]:
                return

            try:
                self.logger.info("creating overlay network")
                self.machine.ssh(node.name, "sudo docker network create --driver overlay --subnet=10.0.9.0/24 gluunet")
                node.state_attrs["state_network_create"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as exc:
                db.session.rollback()
                self.logger.error("failed to create overlay network")
                self.logger.error(exc)


class DeployWorkerNode(DeployNode):
    def __init__(self, node_model_obj, discovery, app):
        super(DeployWorkerNode, self).__init__(node_model_obj, app)
        self.discovery = discovery

    @run_in_reactor
    def deploy(self):
        self._node_create()
        self._rng_tools()
        self._pull_images()
        self._is_completed()

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def _is_completed(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)
            if all([node.state_attrs["state_node_create"],
                    node.state_attrs["state_rng_tools"],
                    node.state_attrs["state_pull_images"]]):
                node.state_attrs["state_complete"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
                self.logger.info('node deployment is done')

    def _node_create(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if node.state_attrs["state_node_create"]:
                return

            try:
                self.logger.info('creating {} node ({})'.format(node.name, node.type))
                self.machine.create(node, self.provider, self.discovery)
                node.state_attrs["state_node_create"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to create node')
                self.logger.error(e)


class DeployMsgconNode(DeployNode):
    def __init__(self, node_model_obj, discovery, app):
        super(DeployMsgconNode, self).__init__(node_model_obj, app)
        self.discovery = discovery

    @run_in_reactor
    def deploy(self):
        self._node_create()
        self._pull_images()
        self._install_mysql()
        self._install_activemq()
        self._install_msgcon()
        self._is_completed()

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def _node_create(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if node.state_attrs["state_node_create"]:
                return

            try:
                self.logger.info('creating {} node ({})'.format(node.name, node.type))
                self.machine.create(node, self.provider, self.discovery)
                node.state_attrs["state_node_create"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to create {} node'.format(node.type))
                self.logger.error(e)

    def _pull_images(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if node.state_attrs["state_pull_images"]:
                return

            try:
                self.logger.info("pulling images in {} node".format(node.name))
                cmd_list = [
                    'sudo docker pull mysql:5',
                    'sudo docker pull rmohr/activemq',
                    'sudo docker pull gluufederation/msgcon',
                ]
                self.machine.ssh(node.name, ' && '.join(cmd_list))
                node.state_attrs["state_pull_images"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to pull images in msgcon node')
                self.logger.error(e)

    def _install_mysql(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if not node.state_attrs["state_pull_images"]:
                return

            if node.state_attrs["state_install_mysql"]:
                return

            self.logger.info('installing mysql in msgcon node')
            try:
                #FIXIT add security
                self.machine.ssh(
                    node.name,
                    'sudo docker run -d --name=msgcon_mysql --restart=always mysql:5',
                )
                node.state_attrs["state_install_mysql"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to install mysql in msgcon node')
                self.logger.error(e)

    def _install_activemq(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if not node.state_attrs["state_pull_images"]:
                return

            if node.state_attrs["state_install_activemq"]:
                return

            self.logger.info('installing activemq')
            try:
                #FIXIT add security
                self.machine.ssh(node.name, 'docker run -d --name=msgcon_activemq --restart=always rmohr/activemq')
                node.state_attrs["state_install_activemq"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to install activemq')
                self.logger.error(e)

    def _install_msgcon(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if not node.state_attrs["state_node_create"]:
                return

            if not node.state_attrs["state_pull_images"]:
                return

            if node.state_attrs["state_install_msgcon"]:
                return

            self.logger.info('installing msgcon')
            try:
                self.machine.ssh(
                    node.name,
                    " ".join([
                        "docker run -d --name=msgcon"
                        "--link msgcon_activemq:activemq"
                        "--link msgcon_mysql:mysql"
                        "-v /opt/msgcon/conf:/etc/message-consumer"
                        "gluufederation/msgcon",
                    ])
                )
                node.state_attrs["state_install_msgcon"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
            except RuntimeError as e:
                db.session.rollback()
                self.logger.error('failed to install msgcon')
                self.logger.error(e)

    def _is_completed(self):
        with self.app.app_context():
            node = Node.query.get(self.node_id)

            if all([node.state_attrs["state_node_create"],
                    node.state_attrs["state_install_mysql"],
                    node.state_attrs["state_install_activemq"],
                    node.state_attrs["state_install_msgcon"],
                    node.state_attrs["state_pull_images"]]):
                node.state_attrs["state_complete"] = True
                flag_modified(node, "state_attrs")
                db.session.commit()
                self.logger.info('node deployment is done')
