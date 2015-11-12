# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import time

from .base import BaseSetup


class NginxSetup(BaseSetup):
    def render_https_conf(self):
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "cert_file": "/etc/certs/nginx.crt",
            "key_file": "/etc/certs/nginx.key",
            "oxauth_nodes": self.cluster.get_oxauth_objects(),
            "oxidp_nodes": self.cluster.get_oxidp_objects(),
            "oxtrust_nodes": self.cluster.get_oxtrust_objects(),
        }

        src = "nodes/nginx/gluu_https.conf"
        dest = "/etc/nginx/sites-available/gluu_https.conf"
        self.copy_rendered_jinja_template(src, dest, ctx)

    def configure_vhost(self):
        rm_cmd = "rm /etc/nginx/sites-enabled/default"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [rm_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        symlink_cmd = "ln -sf /etc/nginx/sites-available/gluu_https.conf " \
                      "/etc/nginx/sites-enabled/gluu_https.conf"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [symlink_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def add_auto_startup_entry(self):
        payload = """
[program:{}]
command=/usr/sbin/nginx -g "daemon off;"
""".format(self.node.type)
        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def restart_nginx(self):
        self.logger.info("restarting nginx")
        service_cmd = "supervisorctl restart nginx"
        self.salt.cmd(self.node.id, "cmd.run", [service_cmd])

    def setup(self):
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.gen_cert("nginx", self.cluster.decrypted_admin_pw,
                      "www-data", "www-data", hostname)
        self.change_cert_access("www-data", "www-data")
        self.render_https_conf()
        self.configure_vhost()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        return True

    def notify_oxtrust(self):
        # a hack to avoid circular import
        from .oxtrust_setup import OxtrustSetup

        try:
            oxtrust = self.provider.get_node_objects(type_="oxtrust")[0]
            setup_obj = OxtrustSetup(oxtrust, self.cluster,
                                     self.app, logger=self.logger)

            setup_obj.delete_nginx_cert()
            setup_obj.remove_host_entries(self.node)

            # wait before telling oxtrust to find nginx node
            time.sleep(2)
            setup_obj.discover_nginx()
        except IndexError:
            pass

    def after_setup(self):
        if self.provider.type == "master":
            self.notify_oxtrust()

    def teardown(self):
        if self.provider.type == "master":
            self.notify_oxtrust()
        self.after_teardown()
