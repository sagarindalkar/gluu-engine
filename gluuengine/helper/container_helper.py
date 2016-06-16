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

from .node_helper import distribute_cluster_data
# from .prometheus_helper import PrometheusHelper
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
from ..machine import Machine
from ..dockerclient import Docker
from ..weave import Weave


class BaseContainerHelper(object):
    __metaclass__ = abc.ABCMeta

    port_bindings = {}

    volumes = {}

    ulimits = []

    @abc.abstractproperty
    def setup_class(self):
        """container setup class. Must be overriden in subclass.
        """

    def __init__(self, container, app, logpath=None):
        self.container = container
        self.app = app
        with self.app.app_context():
            self.cluster = db.get(self.container.cluster_id, "clusters")
            self.node = db.get(self.container.node_id, "nodes")

        if logpath:
            self.logger = create_file_logger(logpath, name=self.container.name)
        else:
            self.logger = logging.getLogger(
                __name__ + "." + self.__class__.__name__,
            )

        mc = Machine()

        with self.app.app_context():
            try:
                master_node = db.search_from_table(
                    "nodes", {"type": "master"},
                )[0]
            except IndexError:
                master_node = self.node

        self.docker = Docker(
            mc.config(self.node.name),
            mc.swarm_config(master_node.name),
            logger=self.logger,
        )

        self.weave = Weave(self.node, self.app, logger=self.logger)
        # self.prometheus = PrometheusHelper(self.app, logger=self.logger)

    @run_in_reactor
    def setup(self, connect_delay=10, exec_delay=15):
        self.mp_setup()

    def mp_setup(self, connect_delay=10, exec_delay=15):
        """Runs the container setup.

        :param connect_delay: Time to wait before start connecting to minion.
        :param exec_delay: Time to wait before start executing remote command.
        """
        try:
            self.logger.info("{} setup is started".format(self.container.image))
            start = time.time()

            # get docker bridge IP as it's where weavedns runs
            bridge_ip, dns_search = self.weave.dns_args()

            cid = self.docker.setup_container(
                name=self.container.name,
                image=self.container.image,
                env=[
                    "constraint:node=={}".format(self.node.name),
                ],
                port_bindings=self.port_bindings,
                volumes=self.volumes,
                dns=[bridge_ip],
                dns_search=[dns_search],
                ulimits=self.ulimits,
                # hostname=self.container.hostname,
            )

            # container is not running
            if not cid:
                self.logger.error("Failed to start the "
                                  "{!r} container".format(self.container.name))
                self.on_setup_error()
                return

            # container.cid in short format
            self.container.cid = cid[:12]
            # self.container.ip = self.docker.get_container_ip(self.container.cid)
            self.container.hostname = "{}.{}.{}".format(
                self.container.cid, self.container.type, dns_search.rstrip("."),
            )

            with self.app.app_context():
                time.sleep(1)
                db.update_to_table(
                    "containers",
                    {"name": self.container.name},
                    self.container,
                )

            # # attach weave IP to container
            # cidr = "{}/{}".format(self.container.weave_ip,
            #                       self.container.weave_prefixlen)
            # self.weave.attach(cidr, self.container.cid)

            # add DNS record
            self.weave.dns_add(self.container.cid, self.container.hostname)

            if self.container.type == "ldap":
                # useful for failover in ox apps
                self.weave.dns_add(
                    self.container.cid,
                    "{}.{}".format(self.container.type, dns_search.rstrip(".")),
                )

            if self.container.type == "nginx":
                self.weave.dns_add(self.container.cid, self.cluster.ox_cluster_hostname)

            setup_obj = self.setup_class(self.container, self.cluster,
                                         self.app, logger=self.logger)
            setup_obj.setup()

            # mark container as SUCCESS
            self.container.state = STATE_SUCCESS

            with self.app.app_context():
                time.sleep(1)
                db.update_to_table(
                    "containers",
                    {"name": self.container.name},
                    self.container,
                )

            # after_setup must be called after container has been marked
            # as SUCCESS
            setup_obj.after_setup()
            setup_obj.remove_build_dir()

            # # updating prometheus
            # self.prometheus.update()

            elapsed = time.time() - start
            self.logger.info("{} setup is finished ({} seconds)".format(
                self.container.image, elapsed
            ))
        except Exception:
            self.logger.error(exc_traceback())
            self.on_setup_error()
        finally:
            # mark containerLog as finished
            with self.app.app_context():
                container_log = db.get(self.container.name, "container_logs")
                if container_log:
                    # avoid concurrent writes, see https://github.com/msiemens/tinydb/issues/91
                    time.sleep(1)

                    container_log.state = STATE_SETUP_FINISHED
                    db.update(container_log.id, container_log, "container_logs")

            # distribute recovery data
            # distribute_cluster_data(self.app.config["DATABASE_URI"])
            distribute_cluster_data(self.app.config["SHARED_DATABASE_URI"],
                                    self.app)

            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)

    def on_setup_error(self):
        """Callback that supposed to be called when error occurs in setup
        process.
        """
        self.logger.info("stopping container {}".format(self.container.name))

        try:
            self.docker.stop_container(self.container.name)
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
                             "created yet or missing".format(self.container.name))

        # mark container as FAILED
        self.container.state = STATE_FAILED

        with self.app.app_context():
            time.sleep(1)
            db.update_to_table(
                "containers",
                {"name": self.container.name},
                self.container,
            )

    @run_in_reactor
    def teardown(self):
        self.logger.info("{} teardown is started".format(self.container.image))
        start = time.time()

        # only do teardown on container with SUCCESS and DISABLED status
        # to avoid unnecessary ops (e.g. propagating nginx changes,
        # removing LDAP replication, etc.) on non-deployed containers;
        # also, initiate the teardown only if node is exist in database
        # (node data may be deleted in other thread)
        if (self.container.state in (STATE_SUCCESS, STATE_DISABLED,)
                and self.node):
            setup_obj = self.setup_class(
                self.container, self.cluster, self.app, logger=self.logger,
            )
            setup_obj.teardown()
            setup_obj.remove_build_dir()

        try:
            self.docker.remove_container(self.container.name)
        except SSLError:  # pragma: no cover
            self.logger.warn("unable to connect to docker API "
                             "due to SSL connection errors")
        except docker.errors.APIError as exc:
            err_code = exc.response.status_code
            if err_code == 404:
                self.logger.warn(
                    "container {!r} does not exist".format(self.container.name)
                )

        # # updating prometheus
        # self.prometheus.update()

        elapsed = time.time() - start
        self.logger.info("{} teardown is finished ({} seconds)".format(
            self.container.image, elapsed
        ))

        with self.app.app_context():
            # mark containerLog as finished
            container_log = db.get(self.container.name, "container_logs")
            if container_log:
                # avoid concurrent writes, see https://github.com/msiemens/tinydb/issues/91
                time.sleep(1)

                container_log.state = STATE_TEARDOWN_FINISHED
                db.update(container_log.id, container_log, "container_logs")

        # distribute recovery data
        # distribute_cluster_data(self.app.config["DATABASE_URI"])
        distribute_cluster_data(self.app.config["SHARED_DATABASE_URI"],
                                self.app)

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


class LdapContainerHelper(BaseContainerHelper):
    setup_class = LdapSetup
    ulimits = [
        {"name": "nofile", "soft": 65536, "hard": 131072},
    ]

    def __init__(self, container, app, logpath=None):
        db_volume = os.path.join(app.config["OPENDJ_VOLUME_DIR"], container.name, "db")
        self.volumes = {
            db_volume: {
                "bind": "/opt/opendj/db",
            },
        }
        super(LdapContainerHelper, self).__init__(container, app, logpath)


class OxauthContainerHelper(BaseContainerHelper):
    setup_class = OxauthSetup

    def __init__(self, container, app, logpath=None):
        self.volumes = {
            # "/var/gluu/webapps/oxauth/pages": {
            #     'bind': '/var/gluu/webapps/oxauth/pages',
            # },
            # "/var/gluu/webapps/oxauth/resources": {
            #     'bind': '/var/gluu/webapps/oxauth/resources',
            # },
            # "/var/gluu/webapps/oxauth/libs": {
            #     'bind': '/var/gluu/webapps/oxauth/libs',
            # },
        }
        super(OxauthContainerHelper, self).__init__(container, app, logpath)


class OxtrustContainerHelper(BaseContainerHelper):
    setup_class = OxtrustSetup
    port_bindings = {8443: ("127.0.0.1", 8443)}

    def __init__(self, container, app, logpath=None):
        self.volumes = {
            "/opt/idp": {
                "bind": "/opt/idp",
            },
            # "/var/gluu/webapps/oxtrust/pages": {
            #     'bind': '/var/gluu/webapps/oxtrust/pages',
            # },
            # "/var/gluu/webapps/oxtrust/resources": {
            #     'bind': '/var/gluu/webapps/oxtrust/resources',
            # },
            # "/var/gluu/webapps/oxtrust/libs": {
            #     'bind': '/var/gluu/webapps/oxtrust/libs',
            # },
        }
        super(OxtrustContainerHelper, self).__init__(container, app, logpath)


class OxidpContainerHelper(BaseContainerHelper):
    setup_class = OxidpSetup


class NginxContainerHelper(BaseContainerHelper):
    setup_class = NginxSetup
    port_bindings = {80: ("0.0.0.0", 80), 443: ("0.0.0.0", 443)}


class OxasimbaContainerHelper(BaseContainerHelper):
    setup_class = OxasimbaSetup
