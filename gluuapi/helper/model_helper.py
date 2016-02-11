# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import abc
import os
import time
import uuid

import docker.errors
from flask import current_app
from requests.exceptions import SSLError
from requests.exceptions import ConnectionError
from crochet import run_in_reactor

from ..database import db
from ..model import LdapNode
from ..model import OxauthNode
from ..model import OxtrustNode
from ..model import OxidpNode
from ..model import NginxNode
from ..model import STATE_SUCCESS
from ..model import STATE_FAILED
from .docker_helper import DockerHelper
from .salt_helper import SaltHelper
from .salt_helper import prepare_minion
from .provider_helper import distribute_cluster_data
from .prometheus_helper import PrometheusHelper
from .weave_helper import WeaveHelper
from ..setup import LdapSetup
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import OxidpSetup
from ..setup import NginxSetup
from ..log import create_file_logger
from ..utils import exc_traceback


class BaseModelHelper(object):
    __metaclass__ = abc.ABCMeta

    port_bindings = {}

    volumes = {}

    ulimits = []

    @abc.abstractproperty
    def setup_class(self):
        """Node setup class. Must be overriden in subclass.
        """

    @abc.abstractproperty
    def node_class(self):
        """Node model class. Must be overriden in subclass.
        """

    @abc.abstractproperty
    def image(self):
        """Docker image name. Must be overriden in subclass.
        """

    def __init__(self, cluster, provider, app):
        self.salt_master_ipaddr = app.config["SALT_MASTER_IPADDR"]
        self.log_dir = app.config["LOG_DIR"]
        self.cluster = cluster
        self.provider = provider

        self.node = self.node_class()
        self.node.cluster_id = cluster.id
        self.node.provider_id = provider.id
        self.node.name = "{}_{}".format(self.image, uuid.uuid4())

        self.logpath = os.path.join(self.log_dir, self.node.name + "-setup.log")
        self.node.setup_logpath = self.logpath
        self.logger = create_file_logger(self.logpath, name=self.node.name)

        self.docker = DockerHelper(self.provider, logger=self.logger)
        self.salt = SaltHelper()
        self.app = current_app._get_current_object()
        self.template_dir = app.config["TEMPLATES_DIR"]
        self.database_uri = app.config["DATABASE_URI"]
        self.weave = WeaveHelper(self.provider, self.app, logger=self.logger)

    @run_in_reactor
    def setup(self, connect_delay=10, exec_delay=15):
        """Runs the node setup.

        :param connect_delay: Time to wait before start connecting to minion.
        :param exec_delay: Time to wait before start executing remote command.
        """
        try:
            # get docker bridge IP as it's where weavedns runs
            bridge_ip = self.weave.docker_bridge_ip()

            container_id = self.docker.setup_container(
                self.node.name,
                self.image,
                env={
                    "SALT_MASTER_IPADDR": os.environ.get("SALT_MASTER_IPADDR"),
                },
                port_bindings=self.port_bindings,
                volumes=self.volumes,
                dns=[bridge_ip],
                dns_search=["gluu.local"],
                ulimits=self.ulimits,
            )

            # container is not running
            if not container_id:
                self.logger.error("Failed to start the "
                                  "{!r} container".format(self.node.name))
                self.on_setup_error()
                return

            # container ID in short format
            self.node.id = container_id[:12]
            prepare_minion(
                self.node.id,
                connect_delay=connect_delay,
                exec_delay=exec_delay,
                logger=self.logger,
            )

            # minion is not connected
            if not self.salt.is_minion_registered(self.node.id):
                self.logger.error("minion {} is "
                                  "unreachable".format(self.node.id))
                self.on_setup_error()
                return

            self.node.ip = self.docker.get_container_ip(self.node.id)
            self.node.domain_name = "{}.{}.gluu.local".format(
                self.node.id, self.node.type,
            )
            db.update_to_table(
                "nodes",
                db.where("name") == self.node.name,
                self.node,
            )

            # attach weave IP to container
            cidr = "{}/{}".format(self.node.weave_ip,
                                  self.node.weave_prefixlen)
            self.weave.attach(cidr, self.node.id)

            # add DNS record
            self.weave.dns_add(self.node.id, self.node.domain_name)

            self.logger.info("{} setup is started".format(self.image))
            start = time.time()

            setup_obj = self.setup_class(self.node, self.cluster,
                                         self.app, logger=self.logger)
            setup_obj.setup()

            # mark node as SUCCESS
            self.node.state = STATE_SUCCESS
            db.update_to_table(
                "nodes",
                db.where("name") == self.node.name,
                self.node,
            )

            # after_setup must be called after node has been marked
            # as SUCCESS
            setup_obj.after_setup()
            setup_obj.remove_build_dir()

            # updating prometheus
            prometheus = PrometheusHelper(self.app)
            prometheus.update()

            elapsed = time.time() - start
            self.logger.info("{} setup is finished ({} seconds)".format(
                self.image, elapsed
            ))
        except Exception:
            self.logger.error(exc_traceback())
            self.on_setup_error()
        finally:
            distribute_cluster_data(self.database_uri)

    def on_setup_error(self):
        """Callback that supposed to be called when error occurs in setup
        process.
        """
        self.logger.info("stopping node {}".format(self.node.name))

        try:
            self.docker.stop(self.node.name)
        except SSLError:
            self.logger.warn("unable to connect to docker API "
                             "due to SSL connection errors")
        except ConnectionError:
            self.logger.warn("unable to connect to docker API "
                             "due to connection errors")
        except docker.errors.NotFound:
            # in case docker.stop raises 404 error code
            # when docker failed to create container
            self.logger.warn("can't find container {}; likely it's not "
                             "created yet or missing".format(self.node.name))
        self.salt.unregister_minion(self.node.id)

        # mark node as FAILED
        self.node.state = STATE_FAILED

        db.update_to_table(
            "nodes",
            db.where("name") == self.node.name,
            self.node,
        )


class LdapModelHelper(BaseModelHelper):
    setup_class = LdapSetup
    node_class = LdapNode
    image = "gluuopendj"
    ulimits = [
        {"name": "nofile", "soft": 65536, "hard": 131072},
    ]


class OxauthModelHelper(BaseModelHelper):
    setup_class = OxauthSetup
    node_class = OxauthNode
    image = "gluuoxauth"


class OxtrustModelHelper(BaseModelHelper):
    setup_class = OxtrustSetup
    node_class = OxtrustNode
    image = "gluuoxtrust"
    port_bindings = {8443: ("127.0.0.1", 8443)}

    def __init__(self, cluster, provider, app):
        self.volumes = {
            app.config["OXIDP_VOLUMES_DIR"]: {
                "bind": "/opt/idp",
            },
        }
        super(OxtrustModelHelper, self).__init__(cluster, provider, app)


class OxidpModelHelper(BaseModelHelper):
    setup_class = OxidpSetup
    node_class = OxidpNode
    image = "gluuoxidp"


class NginxModelHelper(BaseModelHelper):
    setup_class = NginxSetup
    node_class = NginxNode
    image = "gluunginx"
    port_bindings = {80: ("0.0.0.0", 80), 443: ("0.0.0.0", 443)}
