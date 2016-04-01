# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import abc
import os
import logging
import time

import docker.errors
from requests.exceptions import SSLError
from requests.exceptions import ConnectionError
from crochet import run_in_reactor

from .docker_helper import DockerHelper
from .salt_helper import SaltHelper
from .salt_helper import prepare_minion
from .provider_helper import distribute_cluster_data
from .prometheus_helper import PrometheusHelper
from .weave_helper import WeaveHelper
from ..database import db
from ..model import STATE_SUCCESS
from ..model import STATE_FAILED
from ..model import STATE_DISABLED
from ..model import STATE_SETUP_FINISHED
from ..model import STATE_TEARDOWN_FINISHED
from ..setup import LdapSetup
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import OxidpSetup
from ..setup import NginxSetup
from ..setup import OxasimbaSetup
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

    def __init__(self, node, app, logpath=None):
        self.node = node
        self.cluster = db.get(self.node.cluster_id, "clusters")
        self.provider = db.get(self.node.provider_id, "providers")

        if logpath:
            self.logger = create_file_logger(logpath, name=self.node.name)
        else:
            self.logger = logging.getLogger(
                __name__ + "." + self.__class__.__name__,
            )

        self.app = app
        self.docker = DockerHelper(self.provider, logger=self.logger)
        self.salt = SaltHelper()
        self.weave = WeaveHelper(self.provider, self.app, logger=self.logger)
        self.prometheus = PrometheusHelper(self.app, logger=self.logger)

    @run_in_reactor
    def setup(self, connect_delay=10, exec_delay=15):
        """Runs the node setup.

        :param connect_delay: Time to wait before start connecting to minion.
        :param exec_delay: Time to wait before start executing remote command.
        """
        try:
            self.logger.info("{} setup is started".format(self.node.image))
            start = time.time()

            # get docker bridge IP as it's where weavedns runs
            bridge_ip = self.weave.docker_bridge_ip()

            container_id = self.docker.setup_container(
                self.node.name,
                self.node.image,
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

            if self.node.type == "ldap":
                self.weave.dns_add(self.node.id, "ldap.gluu.local")

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
            self.prometheus.update()

            elapsed = time.time() - start
            self.logger.info("{} setup is finished ({} seconds)".format(
                self.node.image, elapsed
            ))
        except Exception:
            self.logger.error(exc_traceback())
            self.on_setup_error()
        finally:
            # mark NodeLog as finished
            node_log = db.get(self.node.name, "node_logs")
            if node_log:
                node_log.state = STATE_SETUP_FINISHED
                db.update(node_log.id, node_log, "node_logs")

            # distribute recovery data
            distribute_cluster_data(self.app.config["DATABASE_URI"])

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

    @run_in_reactor
    def teardown(self):
        self.logger.info("{} teardown is started".format(self.node.image))
        start = time.time()

        # only do teardown on node with SUCCESS and DISABLED status
        # to avoid unnecessary ops (e.g. propagating nginx changes,
        # removing LDAP replication, etc.) on non-deployed nodes
        if self.node.state in (STATE_SUCCESS, STATE_DISABLED,):
            setup_obj = self.setup_class(
                self.node, self.cluster, self.app, logger=self.logger,
            )
            setup_obj.teardown()
            setup_obj.remove_build_dir()

        try:
            self.docker.remove_container(self.node.name)
        except SSLError:  # pragma: no cover
            self.logger.warn("unable to connect to docker API "
                             "due to SSL connection errors")

        self.salt.unregister_minion(self.node.id)

        # updating prometheus
        self.prometheus.update()

        elapsed = time.time() - start
        self.logger.info("{} teardown is finished ({} seconds)".format(
            self.node.image, elapsed
        ))

        # mark NodeLog as finished
        node_log = db.get(self.node.name, "node_logs")
        if node_log:
            node_log.state = STATE_TEARDOWN_FINISHED
            db.update(node_log.id, node_log, "node_logs")

        # distribute recovery data
        distribute_cluster_data(self.app.config["DATABASE_URI"])


class LdapModelHelper(BaseModelHelper):
    setup_class = LdapSetup
    ulimits = [
        {"name": "nofile", "soft": 65536, "hard": 131072},
    ]

    def __init__(self, node, app, logpath=None):
        db_volume = os.path.join(app.config["OPENDJ_VOLUME_DIR"], node.name, "db")
        self.volumes = {
            db_volume: {
                "bind": "/opt/opendj/db",
            },
        }
        super(LdapModelHelper, self).__init__(node, app, logpath)


class OxauthModelHelper(BaseModelHelper):
    setup_class = OxauthSetup

    def __init__(self, node, app, logpath=None):
        self.volumes = {
            "/var/gluu/webapps/oxauth": {
                'bind': '/var/gluu/webapps/oxauth',
            },
        }
        super(OxauthModelHelper, self).__init__(node, app, logpath)


class OxtrustModelHelper(BaseModelHelper):
    setup_class = OxtrustSetup
    port_bindings = {8443: ("127.0.0.1", 8443)}

    def __init__(self, node, app, logpath=None):
        self.volumes = {
            app.config["OXIDP_OVERRIDE_DIR"]: {
                "bind": "/opt/idp",
            },
            "/var/gluu/webapps/identity": {
                'bind': '/var/gluu/webapps/identity',
            },
        }
        super(OxtrustModelHelper, self).__init__(node, app, logpath)


class OxidpModelHelper(BaseModelHelper):
    setup_class = OxidpSetup


class NginxModelHelper(BaseModelHelper):
    setup_class = NginxSetup
    port_bindings = {80: ("0.0.0.0", 80), 443: ("0.0.0.0", 443)}


class OxasimbaModelHelper(BaseModelHelper):
    setup_class = OxasimbaSetup
