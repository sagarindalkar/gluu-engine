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

from ..database import db
from ..model import STATE_SUCCESS
from ..model import STATE_FAILED
from ..model import STATE_DISABLED
from ..model import STATE_SETUP_FINISHED
from ..model import STATE_TEARDOWN_FINISHED
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import OxidpSetup
from ..setup import NginxSetup
from ..setup import OxasimbaSetup
from ..setup import OxelevenSetup
from ..log import create_file_logger
from ..utils import exc_traceback
from ..machine import Machine
from ..dockerclient import Docker


class BaseContainerHelper(object):
    __metaclass__ = abc.ABCMeta

    port_bindings = {}

    ulimits = []

    @abc.abstractproperty
    def setup_class(self):
        """container setup class. Must be overriden in subclass.
        """

    def __init__(self, container, app, logpath=None):
        self.container = container
        self.app = app
        self.cluster = db.get(self.container.cluster_id, "clusters")
        self.node = db.get(self.container.node_id, "nodes")

        log_level = logging.DEBUG if self.app.config["DEBUG"] else logging.INFO
        if logpath:
            self.logger = create_file_logger(logpath, log_level=log_level,
                                             name=self.container.name)
        else:
            self.logger = logging.getLogger(
                __name__ + "." + self.__class__.__name__,
            )
            self.logger.setLevel(log_level)

        mc = Machine()

        try:
            master_node = db.search_from_table(
                "nodes", {"type": "master"},
            )[0]
        except IndexError:
            master_node = self.node

        self.docker = Docker(
            mc.config(self.node.name),
            mc.swarm_config(master_node.name),
        )

    @run_in_reactor
    def setup(self):
        self.mp_setup()

    def mp_setup(self):
        """Runs the container setup.
        """
        try:
            self.logger.info("{} setup is started".format(self.container.name))
            start = time.time()

            cid = self.docker.setup_container(
                name=self.container.name,
                image="{}:{}".format(self.container.image,
                                     self.app.config["GLUU_IMAGE_TAG"]),
                env=[
                    "constraint:node=={}".format(self.node.name),
                ],
                port_bindings=self.port_bindings,
                volumes=self.volumes,
                ulimits=self.ulimits,
                command=self.command,
                aliases=self.aliases,
            )

            # container is not running
            if not cid:
                self.logger.error("Failed to start the "
                                  "{!r} container".format(self.container.name))
                self.on_setup_error()
                return

            # container.cid in short format
            self.container.cid = cid[:12]
            self.container.hostname = "{}.{}".format(self.container.cid, self.container.type)

            db.update_to_table(
                "containers",
                {"name": self.container.name},
                self.container,
            )

            setup_obj = self.setup_class(self.container, self.cluster,
                                         self.app, logger=self.logger)
            setup_obj.setup()

            # mark container as SUCCESS
            self.container.state = STATE_SUCCESS

            db.update_to_table(
                "containers",
                {"name": self.container.name},
                self.container,
            )

            # after_setup must be called after container has been marked
            # as SUCCESS
            setup_obj.after_setup()
            setup_obj.remove_build_dir()

            elapsed = time.time() - start
            self.logger.info("{} setup is finished ({} seconds)".format(
                self.container.name, elapsed
            ))
        except Exception:
            self.logger.error(exc_traceback())
            self.on_setup_error()
        finally:
            # mark containerLog as finished
            try:
                container_log = db.search_from_table(
                    "container_logs",
                    {"container_name": self.container.name},
                )[0]
            except IndexError:
                container_log = None

            if container_log:
                container_log.state = STATE_SETUP_FINISHED
                db.update(container_log.id, container_log, "container_logs")

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

        db.update_to_table(
            "containers",
            {"name": self.container.name},
            self.container,
        )

    @run_in_reactor
    def teardown(self):
        self.mp_teardown()

    def mp_teardown(self):
        self.logger.info("{} teardown is started".format(self.container.name))
        start = time.time()

        # only do teardown on container with SUCCESS and DISABLED status
        # to avoid unnecessary ops (e.g. propagating nginx config changes)
        # on non-deployed containers; also, initiate the teardown only if
        # node is exist in database (node data may be deleted in other thread)
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

        elapsed = time.time() - start
        self.logger.info("{} teardown is finished ({} seconds)".format(
            self.container.name, elapsed
        ))

        # mark containerLog as finished
        try:
            container_log = db.search_from_table(
                "container_logs",
                {"container_name": self.container.name},
            )[0]
        except IndexError:
            container_log = None

        if container_log:
            container_log.state = STATE_TEARDOWN_FINISHED
            db.update(container_log.id, container_log, "container_logs")

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    @property
    def command(self):
        return []

    @property
    def volumes(self):
        return {}

    @property
    def aliases(self):
        return [self.container.type]


class OxauthContainerHelper(BaseContainerHelper):
    setup_class = OxauthSetup

    @property
    def volumes(self):
        log_volume = os.path.join(self.app.config["OXAUTH_LOGS_VOLUME_DIR"],
                                  self.container.name,
                                  "logs")
        return {
            "/var/gluu/webapps/oxauth/pages": {
                "bind": "/opt/gluu/jetty/oxauth/custom/pages",
            },
            "/var/gluu/webapps/oxauth/static": {
                "bind": "/opt/gluu/jetty/oxauth/custom/static",
            },
            "/var/gluu/webapps/oxauth/lib": {
                "bind": "/opt/gluu/jetty/oxauth/lib/ext",
            },
            log_volume: {
                "bind": "/opt/gluu/jetty/oxauth/logs",
            },
        }


class OxtrustContainerHelper(BaseContainerHelper):
    setup_class = OxtrustSetup

    @property
    def volumes(self):
        log_volume = os.path.join(self.app.config["OXTRUST_LOGS_VOLUME_DIR"],
                                  self.container.name,
                                  "logs")
        return {
            "/opt/idp": {
                "bind": "/opt/idp",
            },
            "/var/gluu/webapps/oxtrust/pages": {
                "bind": "/opt/gluu/jetty/identity/custom/pages",
            },
            "/var/gluu/webapps/oxtrust/static": {
                "bind": "/opt/gluu/jetty/identity/custom/static",
            },
            "/var/gluu/webapps/oxtrust/lib": {
                "bind": "/opt/gluu/jetty/identity/lib/ext",
            },
            log_volume: {
                "bind": "/opt/gluu/jetty/identity/logs",
            },
        }


class OxidpContainerHelper(BaseContainerHelper):
    setup_class = OxidpSetup

    @property
    def volumes(self):
        log_volume = os.path.join(self.app.config["OXIDP_LOGS_VOLUME_DIR"],
                                  self.container.name,
                                  "logs")
        return {
            log_volume: {
                "bind": "/opt/idp/logs",
            },
        }


class NginxContainerHelper(BaseContainerHelper):
    setup_class = NginxSetup
    port_bindings = {80: ("0.0.0.0", 80,), 443: ("0.0.0.0", 443,)}

    @property
    def aliases(self):
        _aliases = [self.container.type]

        # add domain with ``.local`` suffix, useful for testing cluster without
        # actual public domain
        if self.cluster.ox_cluster_hostname.endswith(".local"):
            _aliases.append(self.cluster.ox_cluster_hostname)
        return _aliases


class OxasimbaContainerHelper(BaseContainerHelper):
    setup_class = OxasimbaSetup

class OxelevenContainerHelper(BaseContainerHelper):
    setup_class = OxelevenSetup
