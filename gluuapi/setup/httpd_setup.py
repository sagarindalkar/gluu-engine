# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os.path
import time

from gluuapi.setup.base import BaseSetup
from gluuapi.setup.oxtrust_setup import OxtrustSetup


class HttpdSetup(BaseSetup):
    def render_https_conf_template(self, hostname):
        src = self.node.https_conf
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        for oxauth in self.cluster.get_oxauth_objects():
            oxauth_ip = oxauth.weave_ip

        for oxtrust in self.cluster.get_oxtrust_objects():
            oxtrust_ip = oxtrust.weave_ip

        ctx = {
            "hostname": hostname,
            "ip": self.node.weave_ip,
            "oxauth_ip": oxauth_ip,
            "oxtrust_ip": oxtrust_ip,
            "httpdCertFn": self.node.httpd_crt,
            "httpdKeyFn": self.node.httpd_key,
            "admin_email": self.cluster.admin_email,
        }
        self.render_template(src, dest, ctx)

    def start_httpd(self):
        self.logger.info("starting httpd")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [["a2enmod ssl headers proxy proxy_http proxy_ajp evasive"],
             ["a2dissite 000-default"],
             ["a2ensite gluu_https"],
             ["service apache2 start"]],
        )

    def setup(self):
        self.logger.info("HTTPd setup is started")
        start = time.time()

        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.create_cert_dir()
        self.gen_cert("httpd", self.cluster.decrypted_admin_pw, "www-data", "www-data", hostname)
        self.change_cert_access("www-data", "www-data")
        self.render_https_conf_template(hostname)
        self.start_httpd()

        elapsed = time.time() - start
        self.logger.info("HTTPd setup is finished ({} seconds)".format(elapsed))
        return True

    def after_setup(self):
        for oxtrust in self.cluster.get_oxtrust_objects():
            setup_obj = OxtrustSetup(oxtrust, self.cluster, logger=self.logger)
            setup_obj.update_host_entries()
            setup_obj.import_httpd_cert()

        # expose the IP
        addr, prefixlen = self.cluster.exposed_weave_ip
        self.salt.cmd(
            self.provider.hostname,
            "cmd.run",
            ["weave expose {}/{}".format(addr, prefixlen)],
        )
        iptables_cmd = "iptables -t nat -A PREROUTING -p tcp " \
                       "-i eth0 --dport 80 -j DNAT " \
                       "--to-destination {}:80".format(self.node.weave_ip)
        self.salt.cmd(self.provider.hostname, "cmd.run", [iptables_cmd])
