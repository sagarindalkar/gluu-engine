# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import logging
import os
import stat
import time

from crochet import run_in_reactor

from .salt_helper import SaltHelper
from .weave_helper import WeaveHelper
from ..database import db


@run_in_reactor
def distribute_cluster_data(src):
    dest = src
    salt = SaltHelper()
    consumer_providers = db.search_from_table(
        "providers", db.where("type") == "consumer"
    )

    for provider in consumer_providers:
        ping = salt.cmd(provider.hostname, "test.ping")
        # wake up the minion (if idle)
        if ping.get(provider.hostname):
            salt.cmd(
                provider.hostname,
                "cmd.run",
                ["mkdir -p {}".format(os.path.dirname(dest))]
            )
            salt.copy_file(provider.hostname, src, dest)


class ProviderHelper(object):
    def __init__(self, provider, app, logger=None):
        self.provider = provider
        self.app = app
        self.weave = WeaveHelper(provider, self.app)
        self.salt = SaltHelper()
        self.logger = logger or logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )

    @run_in_reactor
    def configure(self, connect_delay=10, exec_delay=15):
        self.prepare_minion(connect_delay, exec_delay)
        self.weave.launch()
        self.import_docker_certs()
        distribute_cluster_data(self.app.config["DATABASE_URI"])

    def import_docker_certs(self):
        cert_types = {
            "/etc/docker/cert.pem": self.write_ssl_cert,
            "/etc/docker/key.pem": self.write_ssl_key,
            "/etc/docker/ca.pem": self.write_ca_cert,
        }
        for remote_cert_path, callback in cert_types.items():
            content = self.get_docker_cert(remote_cert_path)
            self.logger.info(
                "importing remote certificate {}".format(remote_cert_path)
            )
            callback(content)

    def get_docker_cert(self, remote_cert_path):
        cat_cmd = "test -f {0} && cat {0}".format(remote_cert_path)
        resp = self.salt.cmd(self.provider.hostname, "cmd.run", [cat_cmd])

        try:
            return resp.get(self.provider.hostname, "")
        except AttributeError:
            # if provider.hostname is not a registered minion, it will
            # returns error string instead of a ``dict``;
            # calling `.get` method in string object will raise AttributeError
            return ""

    def _write_cert_file(self, content, dest, filemode):
        """Writes a file and change the file mode.
        """
        try:
            os.makedirs(self.app.config["DOCKER_CERT_DIR"])
        except OSError as exc:
            # file exists
            if exc.errno == 17:
                pass
            else:  # pragma: no cover
                raise exc

        # temporarily set file as writable only if file exists
        if os.path.exists(dest):
            os.chmod(dest, stat.S_IWUSR)  # pragma: no cover

        with codecs.open(dest, mode="w", encoding="utf-8") as fp:
            fp.write(content)
            os.chmod(dest, filemode)

    def write_ssl_cert(self, content):
        # chmod 444
        self._write_cert_file(content, self.provider.ssl_cert_path,
                              stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    def write_ssl_key(self, content):
        # chmod 400
        self._write_cert_file(content, self.provider.ssl_key_path, stat.S_IRUSR)

    def write_ca_cert(self, content):
        # chmod 444
        self._write_cert_file(content, self.provider.ca_cert_path,
                              stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

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
        self.salt.register_minion(self.provider.hostname)

        # delay the remote execution
        # see https://github.com/saltstack/salt/issues/13561
        # TODO: there must be a way around this
        self.logger.info("Preparing remote execution; sleeping for "
                         "{} seconds".format(exec_delay))
        time.sleep(exec_delay)
