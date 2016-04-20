# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import time

from crochet import run_in_reactor

# from .salt_helper import SaltHelper
from ..database import db
from ..machine import Machine


class WeaveHelper(object):
    # def __init__(self, provider, app, logger=None):
    def __init__(self, node, app, logger=None):
        # self.provider = provider
        self.node = node

        try:
            self.cluster = db.all("clusters")[0]
        except IndexError:
            self.cluster = None

        self.app = app
        # self.salt = SaltHelper()
        self.machine = Machine()
        self.logger = logger or logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.weave_encryption = self.app.config['WEAVE_ENCRYPTION']

    @run_in_reactor
    def launch_async(self):
        """Launches weave container for master or consumer provider
        asynchronously.
        """
        self.launch()

    def launch(self):
        """Launches weave container for master or consumer provider.
        """
        if self.provider.type == "master":
            self.launch_master()
        else:
            # self.launch_consumer()
            self.launch_worker()

        # wait for weave to run before exposing its network
        time.sleep(5)
        self.expose_network()

    def expose_network(self):
        """Exposes gateway IP.
        """
        addr, prefixlen = self.cluster.exposed_weave_ip
        self.logger.info("exposing weave network at {}/{}".format(
            addr, prefixlen
        ))
        # self.salt.cmd(
        #     self.provider.hostname,
        #     "cmd.run",
        #     ["weave expose {}/{}".format(addr, prefixlen)],
        # )
        self.machine.ssh(self.node.name,
                         "weave expose {}/{}".format(addr, prefixlen))

    def launch_master(self):
        """Launches weave router for master node.
        """
        self.logger.info("re-launching weave for master node")
        # stop_cmd = "weave stop"
        # self.salt.cmd(self.provider.hostname, "cmd.run", [stop_cmd])
        self.machine.ssh(self.node.name, "weave stop")
        time.sleep(5)

        ctx = {
            "password": ('--password ' + self.cluster.decrypted_admin_pw) if self.weave_encryption else '',
            "ipnet": self.cluster.weave_ip_network,
        }
        launch_cmd = "weave launch-router {password} " \
                     "--dns-domain gluu.local " \
                     "--ipalloc-range {ipnet} " \
                     "--ipalloc-default-subnet {ipnet}".format(**ctx)
        # self.salt.cmd(self.provider.hostname, "cmd.run", [launch_cmd])
        self.machine.ssh(self.node.name, launch_cmd)

    # def launch_consumer(self):
    def launch_worker(self):
        """Launches weave router for worker node.
        """
        self.logger.info("re-launching weave for worker node")
        # stop_cmd = "weave stop"
        # self.salt.cmd(self.provider.hostname, "cmd.run", [stop_cmd])
        self.machine.ssh(self.node.name, "weave stop")
        time.sleep(5)

        ctx = {
            "password": ('--password ' + self.cluster.decrypted_admin_pw) if self.weave_encryption else '',
            "ipnet": self.cluster.weave_ip_network,
            "master_ipaddr": self.app.config["SALT_MASTER_IPADDR"],
        }
        launch_cmd = "weave launch-router {password} " \
                     "--dns-domain gluu.local " \
                     "--ipalloc-range {ipnet} " \
                     "--ipalloc-default-subnet {ipnet} " \
                     "{master_ipaddr}".format(**ctx)
        # self.salt.cmd(self.provider.hostname, "cmd.run", [launch_cmd])
        self.machine.ssh(self.node.name, launch_cmd)

    def attach(self, cidr, node_id):
        """Adds container into weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        attach_cmd = "weave attach {} {}".format(cidr, node_id)
        self.logger.info("attaching weave IP address {}".format(cidr))
        # jid = self.salt.cmd_async(
        #     self.provider.hostname, "cmd.run", [attach_cmd]
        # )
        # self.salt.subscribe_event(jid, self.provider.hostname)
        self.machine.ssh(self.node.name, attach_cmd)

    def detach(self, cidr, node_id):
        """Removes container from weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        detach_cmd = "weave detach {} {}".format(cidr, node_id)
        self.logger.info("detaching weave IP address {}".format(cidr))
        # jid = self.salt.cmd_async(
        #     self.provider.hostname, "cmd.run", [attach_cmd]
        # )
        # self.salt.subscribe_event(jid, self.provider.hostname)
        self.machine.ssh(self.node.name, detach_cmd)

    def dns_add(self, node_id, domain_name):
        """Adds entry to weave DNS.

        :param node_id: ID of the container/node.
        :param domain_name: Local domain name.
        """
        dns_cmd = "weave dns-add {} -h {}".format(node_id, domain_name)
        self.logger.info("adding {} to local DNS server".format(domain_name))
        # jid = self.salt.cmd_async(self.provider.hostname, "cmd.run", [dns_cmd])
        # self.salt.subscribe_event(jid, self.provider.hostname)
        self.machine.ssh(self.node.name, dns_cmd)

    def docker_bridge_ip(self):
        """Gets IP of docker bridge (docker0) interface.
        """
        # jid = self.salt.cmd_async(
        #     self.provider.hostname, "cmd.run", ["weave docker-bridge-ip"]
        # )
        # resp = self.salt.subscribe_event(jid, self.provider.hostname)
        # return resp["data"]["return"]

        stdout, _, _ = self.machine.ssh(self.node.name, "weave docker-bridge-ip")
        return stdout.strip()
