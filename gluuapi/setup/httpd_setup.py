# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseSetup


class HttpdSetup(BaseSetup):
    def setup(self):
        return True

    def teardown(self):
        self.remove_iptables_rule()
        self.after_teardown()

    def remove_iptables_rule(self):
        # unexpose port 80 and 443
        for port in [80, 443]:
            iptables_cmd = "iptables -t nat -D PREROUTING -p tcp " \
                           "-i eth0 --dport {0} -j DNAT " \
                           "--to-destination {1}:{0}".format(port, self.node.weave_ip)
            self.salt.cmd(self.provider.hostname, "cmd.run", [iptables_cmd])
