# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import time

from crochet import run_in_reactor

from .salt_helper import SaltHelper


class WeaveHelper(object):
    def __init__(self, provider, cluster, master_ipaddr, logger=None):
        self.provider = provider
        self.cluster = cluster
        self.master_ipaddr = master_ipaddr
        self.salt = SaltHelper()
        self.logger = logger or logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )

    @run_in_reactor
    def launch_async(self, register_minion=True):
        self.launch(register_minion)

    def launch(self, register_minion=True):
        if register_minion:
            self.prepare_minion()

        if self.provider.type == "master":
            self.launch_master()
        else:
            self.launch_consumer()

        # wait for weave to run before exposing its network
        time.sleep(5)
        self.expose_network()

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

    def expose_network(self):
        addr, prefixlen = self.cluster.exposed_weave_ip
        self.logger.info("exposing weave network at {}/{}".format(
            addr, prefixlen
        ))
        self.salt.cmd(
            self.provider.hostname,
            "cmd.run",
            ["weave expose {}/{}".format(addr, prefixlen)],
        )

    def launch_master(self):
        self.logger.info("re-launching weave for master provider")
        stop_cmd = "weave stop"
        self.salt.cmd(self.provider.hostname, "cmd.run", [stop_cmd])
        time.sleep(5)
        launch_cmd = "weave launch -password {}".format(
            self.cluster.decrypted_admin_pw,
        )
        self.salt.cmd(self.provider.hostname, "cmd.run", [launch_cmd])

    def launch_consumer(self):
        self.logger.info("re-launching weave for consumer provider")
        stop_cmd = "weave stop"
        self.salt.cmd(self.provider.hostname, "cmd.run", [stop_cmd])
        time.sleep(5)
        launch_cmd = "weave launch -password {} {}".format(
            self.cluster.decrypted_admin_pw,
            self.master_ipaddr,
        )
        self.salt.cmd(self.provider.hostname, "cmd.run", [launch_cmd])
