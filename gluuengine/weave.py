# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from .machine import Machine

# older weave dns-args returns --dns x.x.x.x --dns-search=weave.local.
# whereas newer weave dns-args returns --dns=x.x.x.x --dns-search=weave.local.
DNS_ARGS_RE = re.compile(r"--dns[=|\s](.+) --dns-search=(.+)")


class Weave(object):
    def __init__(self, node, app=None):
        self.node = node
        self.machine = Machine()

    def attach(self, container_id, cidr=""):  # pragma: no cover
        """Adds container into weave network.

        :param cidr: CIDR, e.g. ``10.2.1.1/24``.
        :param node_id: ID of the node/container.
        """
        attach_cmd = "sudo weave attach {} {}".format(cidr, container_id)
        self.machine.ssh(self.node.name, attach_cmd)

    def detach(self, container_id, cidr=""):  # pragma: no cover
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
        dns = None
        dns_search = None
        output = self.machine.ssh(self.node.name, "sudo weave dns-args")

        rgx = DNS_ARGS_RE.match(output)
        if rgx:
            dns, dns_search = rgx.groups()
        return dns, dns_search
