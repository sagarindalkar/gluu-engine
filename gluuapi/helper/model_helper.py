# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time
import uuid

from flask import current_app
from requests.exceptions import SSLError
from requests.exceptions import ConnectionError
from crochet import run_in_reactor

from ..database import db
from ..model import LdapNode
from ..model import OxauthNode
from ..model import OxtrustNode
from ..model import HttpdNode
from ..model import SamlNode
from ..model import STATE_SUCCESS
from ..model import STATE_FAILED
from ..model import STATE_IN_PROGRESS
from .docker_helper import DockerHelper
from .salt_helper import SaltHelper
from .provider_helper import distribute_cluster_data
from .prometheus_helper import PrometheusHelper
from .weave_helper import WeaveHelper
from ..setup import LdapSetup
from ..setup import OxauthSetup
from ..setup import OxtrustSetup
from ..setup import HttpdSetup
from ..setup import SamlSetup
from ..log import create_file_logger
from ..utils import exc_traceback


class BaseModelHelper(object):
    #: Node setup class. Must be overriden in subclass.
    setup_class = None

    #: Node model class. Must be overriden in subclass.
    node_class = None

    #: Docker image name. Must be overriden in subclass.
    image = ""

    #: URL to image's Dockerfile. Must be overriden in subclass.
    dockerfile = ""

    port_bindings = {}

    volumes = {}

    def __init__(self, cluster, provider, salt_master_ipaddr,
                 template_dir, log_dir, database_uri):
        assert self.setup_class, "setup_class must be set"
        assert self.node_class, "node_class must be set"
        assert self.image, "image attribute cannot be empty"
        assert self.dockerfile, "dockerfile attribute cannot be empty"

        self.salt_master_ipaddr = salt_master_ipaddr
        self.cluster = cluster
        self.provider = provider

        self.node = self.node_class()
        self.node.cluster_id = cluster.id
        self.node.provider_id = provider.id
        self.node.name = "{}_{}".format(self.image, uuid.uuid4())

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logpath = os.path.join(log_dir, self.node.name + "-setup.log")
        self.node.setup_logpath = self.logpath
        self.logger = create_file_logger(self.logpath, name=self.node.name)

        self.docker = DockerHelper(self.provider, logger=self.logger)
        self.salt = SaltHelper()
        self.app = current_app._get_current_object()
        self.template_dir = template_dir
        self.database_uri = database_uri
        self.weave = WeaveHelper(self.provider, self.app, logger=self.logger)

    def prepare_minion(self, connect_delay=10, exec_delay=15):
        """Waits for minion to connect before doing any remote execution.
        """
        # wait for 10 seconds to make sure minion connected
        # and sent its key to master
        # TODO: there must be a way around this
        self.logger.info("Waiting for minion to connect; sleeping for "
                         "{} seconds".format(connect_delay))
        time.sleep(connect_delay)

        # register the container as minion
        self.salt.register_minion(self.node.id)

        # delay the remote execution
        # see https://github.com/saltstack/salt/issues/13561
        # TODO: there must be a way around this
        self.logger.info("Preparing remote execution; sleeping for "
                         "{} seconds".format(exec_delay))
        time.sleep(exec_delay)

    @run_in_reactor
    def setup(self, connect_delay=10, exec_delay=15):
        """Runs the node setup.
        """
        try:
            self.node.state = STATE_IN_PROGRESS
            db.persist(self.node, "nodes")

            # get docker bridge IP as it's where weavedns runs
            bridge_ip = self.weave.docker_bridge_ip()

            container_id = self.docker.setup_container(
                self.node.name,
                self.image,
                self.dockerfile,
                self.salt_master_ipaddr,
                port_bindings=self.port_bindings,
                volumes=self.volumes,
                dns=[bridge_ip],
                dns_search=["gluu.local"],
            )

            # container is not running
            if not container_id:
                self.logger.error("Failed to start the "
                                  "{!r} container".format(self.node.name))
                self.on_setup_error()
                return

            # container ID in short format
            self.node.id = container_id[:12]
            self.prepare_minion(connect_delay, exec_delay)

            # minion is not connected
            if not self.salt.is_minion_registered(self.node.id):
                self.logger.error("minion {} is "
                                  "unreachable".format(self.node.id))
                self.on_setup_error()
                return

            self.node.ip = self.docker.get_container_ip(self.node.id)
            self.node.weave_ip = self.cluster.last_fetched_addr
            self.node.weave_prefixlen = self.cluster.prefixlen
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
                                         self.logger, self.template_dir)
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
            prometheus = PrometheusHelper(template_dir=self.template_dir)
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
        self.logger.info("destroying minion {}".format(self.node.name))

        try:
            self.docker.remove_container(self.node.name)
        except SSLError:
            self.logger.warn("unable to connect to docker API "
                             "due to SSL connection errors")
        except ConnectionError:
            self.logger.warn("unable to connect to docker API "
                             "due to connection errors")
        self.salt.unregister_minion(self.node.id)

        # mark node as FAILED
        self.node.state = STATE_FAILED

        # if httpd node is FAILED, remove reference to oxAuth and SAML
        # so we can use those 2 nodes for another httpd node
        if self.node.type == "httpd":
            self.node.oxauth_node_id = ""
            self.node.saml_node_id = ""

        db.update_to_table(
            "nodes",
            db.where("name") == self.node.name,
            self.node,
        )


class LdapModelHelper(BaseModelHelper):
    setup_class = LdapSetup
    node_class = LdapNode
    image = "gluuopendj"
    dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                 "/gluu-docker/master/ubuntu/14.04/gluuopendj/Dockerfile"


class OxauthModelHelper(BaseModelHelper):
    setup_class = OxauthSetup
    node_class = OxauthNode
    image = "gluuoxauth"
    dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                 "/gluu-docker/master/ubuntu/14.04/gluuoxauth/Dockerfile"


class OxtrustModelHelper(BaseModelHelper):
    setup_class = OxtrustSetup
    node_class = OxtrustNode
    image = "gluuoxtrust"
    dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                 "/gluu-docker/master/ubuntu/14.04/gluuoxtrust/Dockerfile"
    port_bindings = {8443: ("127.0.0.1", 8443)}
    volumes = {
        "/etc/gluu/saml": {
            "bind": "/opt/idp",
            "mode": "ro",
        }
    }


class HttpdModelHelper(BaseModelHelper):
    setup_class = HttpdSetup
    node_class = HttpdNode
    image = "gluuhttpd"
    dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                 "/gluu-docker/master/ubuntu/14.04/gluuhttpd/Dockerfile"


class SamlModelHelper(BaseModelHelper):
    setup_class = SamlSetup
    node_class = SamlNode
    image = "gluushib"
    dockerfile = "https://raw.githubusercontent.com/GluuFederation" \
                 "/gluu-docker/master/ubuntu/14.04/gluushib/Dockerfile"
