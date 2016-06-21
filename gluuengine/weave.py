# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from .database import db
from .machine import Machine

# older weave dns-args returns --dns x.x.x.x --dns-search=weave.local.
# whereas newer weave dns-args returns --dns=x.x.x.x --dns-search=weave.local.
DNS_ARGS_RE = re.compile(r"--dns[=|\s](.+) --dns-search=(.+)")


class Weave(object):
    def __init__(self, node, app):
        self.node = node
        self.app = app

        with self.app.app_context():
            try:
                self.master_node = db.search_from_table(
                    "nodes", {"type": "master"},
                )[0]
            except IndexError:
                self.master_node = None

            try:
                self.cluster = db.all("clusters")[0]
            except IndexError:
                self.cluster = None

        self.machine = Machine()
        self.weave_encryption = self.app.config['WEAVE_ENCRYPTION']

    def attach(self, container_id, cidr=""):
        """Adds container into weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        attach_cmd = "sudo weave attach {} {}".format(cidr, container_id)
        self.machine.ssh(self.node.name, attach_cmd)

    def detach(self, container_id, cidr=""):
        """Removes container from weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        detach_cmd = "sudo weave detach {} {}".format(cidr, container_id)
        self.machine.ssh(self.node.name, detach_cmd)

    def dns_add(self, container_id, hostname):
        """Adds entry to weave DNS.

        :param node_id: ID of the container/node.
        :param domain_name: Local domain name.
        """
        dns_cmd = "sudo weave dns-add {} -h {}".format(container_id, hostname)
        self.machine.ssh(self.node.name, dns_cmd)

    def docker_bridge_ip(self):  # pragma: no cover
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
