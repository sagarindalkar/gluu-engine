# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import re
import time

from crochet import run_in_reactor

from .database import db
from .machine import Machine

DNS_ARGS_RE = re.compile(r"--dns (.+) --dns-search=(.+)")


class Weave(object):
    def __init__(self, node, app, logger=None):
        self.node = node

        try:
            self.cluster = db.all("clusters")[0]
        except IndexError:
            self.cluster = None

        self.app = app
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
        # if self.node.type == "master":
        #     self.launch_master()
        # else:
        #     self.launch_worker()

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
        self.machine.ssh(self.node.name,
                         "sudo weave expose {}/{}".format(addr, prefixlen))

    # def launch_master(self):
    #     """Launches weave router for master node.
    #     """
    #     self.logger.info("re-launching weave for master node")
    #     self.machine.ssh(self.node.name, "sudo weave stop")
    #     time.sleep(5)

    #     ctx = {
    #         "password": ('--password ' + self.cluster.decrypted_admin_pw) if self.weave_encryption else '',
    #         "ipnet": self.cluster.weave_ip_network,
    #     }
    #     launch_cmd = "sudo weave launch-router {password} " \
    #                  "--dns-domain gluu.local " \
    #                  "--ipalloc-range {ipnet} " \
    #                  "--ipalloc-default-subnet {ipnet}".format(**ctx)
    #     self.machine.ssh(self.node.name, launch_cmd)

    # def launch_worker(self):
    #     """Launches weave router for worker node.
    #     """
    #     self.logger.info("re-launching weave for worker node")
    #     self.machine.ssh(self.node.name, "weave stop")
    #     time.sleep(5)

    #     ctx = {
    #         "password": ('--password ' + self.cluster.decrypted_admin_pw) if self.weave_encryption else '',
    #         "ipnet": self.cluster.weave_ip_network,
    #         "master_ipaddr": self.app.config["SALT_MASTER_IPADDR"],
    #     }
    #     launch_cmd = "sudo weave launch-router {password} " \
    #                  "--dns-domain gluu.local " \
    #                  "--ipalloc-range {ipnet} " \
    #                  "--ipalloc-default-subnet {ipnet} " \
    #                  "{master_ipaddr}".format(**ctx)
    #     self.machine.ssh(self.node.name, launch_cmd)

    def attach(self, cidr, node_id):
        """Adds container into weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        attach_cmd = "sudo weave attach {} {}".format(cidr, node_id)
        self.logger.info("attaching weave IP address {}".format(cidr))
        self.machine.ssh(self.node.name, attach_cmd)

    def detach(self, cidr, node_id):
        """Removes container from weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        detach_cmd = "sudo weave detach {} {}".format(cidr, node_id)
        self.logger.info("detaching weave IP address {}".format(cidr))
        self.machine.ssh(self.node.name, detach_cmd)

    def dns_add(self, node_id, hostname):
        """Adds entry to weave DNS.

        :param node_id: ID of the container/node.
        :param domain_name: Local domain name.
        """
        dns_cmd = "sudo weave dns-add {} -h {}".format(node_id, hostname)
        self.logger.info("adding {} to local DNS server".format(hostname))
        self.machine.ssh(self.node.name, dns_cmd)

    def docker_bridge_ip(self):
        """Gets IP of docker bridge (docker0) interface.
        """
        return self.machine.ssh(self.node.name, "sudo weave docker-bridge-ip")

    def dns_args(self):
        """Gets DNS arguments.

        :returns: A tuple consists of docker bridge IP and DNS search
        """
        bridge_ip = None
        dns_search = None
        output = self.machine.ssh(self.node.name, "sudo weave dns-args")

        rgx = DNS_ARGS_RE.match(output)
        if rgx:
            bridge_ip, dns_search = rgx.groups()
        return bridge_ip, dns_search
