# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time

from .base import BaseSetup
from .oxtrust_setup import OxtrustSetup


class HttpdSetup(BaseSetup):
    def render_https_conf_template(self, hostname):
        src = "nodes/httpd/gluu_https.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        oxauth = self.node.get_oxauth_object()
        saml = self.node.get_saml_object()

        ctx = {
            "hostname": hostname,
            "ip": self.node.weave_ip,
            "oxauth": oxauth,
            "saml": saml,
            "httpd_cert_fn": self.node.httpd_crt,
            "httpd_key_fn": self.node.httpd_key,
            "admin_email": self.cluster.admin_email,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def start_httpd(self):
        self.logger.info("starting httpd")

        a2enmod_cmd = "a2enmod ssl headers proxy proxy_http proxy_ajp"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2enmod_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        a2dissite_cmd = "a2dissite 000-default"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2dissite_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        a2ensite_cmd = "a2ensite gluu_https"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2ensite_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        service_cmd = "service apache2 start"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [service_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def add_auto_startup_entry(self):
        # other ways to start apache2
        # [program:apache2]
        # command=/bin/bash -c "source /etc/apache2/envvars && exec /usr/sbin/apache2 -DFOREGROUND"
        # OR
        # [program:apache2]
        # command=/usr/sbin/apachectl start

        # add supervisord entry
        run_cmd = '/bin/bash -c "service apache2 start"'
        payload = """
[program:{}]
command={}
""".format(self.node.type, run_cmd)

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def setup(self):
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.create_cert_dir()
        self.gen_cert("httpd", self.cluster.decrypted_admin_pw,
                      "www-data", "www-data", hostname)
        self.change_cert_access("www-data", "www-data")
        self.render_https_conf_template(hostname)
        # add auto startup entry
        self.add_auto_startup_entry()
        self.start_httpd()
        return True

    def after_setup(self):
        try:
            oxtrust = self.provider.get_node_objects(type_="oxtrust")[0]
            setup_obj = OxtrustSetup(oxtrust, self.cluster,
                                     self.app, logger=self.logger)
            setup_obj.delete_httpd_cert()
            setup_obj.remove_host_entries(self.node)

            # tell oxtrust to find another httpd node
            time.sleep(2)
            setup_obj.discover_httpd()
        except IndexError:
            pass

        # clear iptables rule for this node
        self.remove_iptables_rule()
        self.add_iptables_rule()

    def teardown(self):
        try:
            oxtrust = self.provider.get_node_objects(type_="oxtrust")[0]
            setup_obj = OxtrustSetup(oxtrust, self.cluster,
                                     self.app, logger=self.logger)
            setup_obj.delete_httpd_cert()
            setup_obj.remove_host_entries(self.node)

            # tell oxtrust to find another httpd node
            time.sleep(2)
            setup_obj.discover_httpd()
        except IndexError:
            pass

        self.remove_iptables_rule()
        self.after_teardown()

    def add_iptables_rule(self):
        # expose port 80 and 443
        for port in [80, 443]:
            iptables_cmd = "iptables -t nat -A PREROUTING -p tcp " \
                           "-i eth0 --dport {0} -j DNAT " \
                           "--to-destination {1}:{0}".format(port, self.node.weave_ip)
            self.salt.cmd(self.provider.hostname, "cmd.run", [iptables_cmd])

    def remove_iptables_rule(self):
        # unexpose port 80 and 443
        for port in [80, 443]:
            iptables_cmd = "iptables -t nat -D PREROUTING -p tcp " \
                           "-i eth0 --dport {0} -j DNAT " \
                           "--to-destination {1}:{0}".format(port, self.node.weave_ip)
            self.salt.cmd(self.provider.hostname, "cmd.run", [iptables_cmd])
