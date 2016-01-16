# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import time

from .base import BaseSetup
from ..model import STATE_SUCCESS


class NginxSetup(BaseSetup):
    def get_session_affinity(self):
        ngx_cmd = "nginx -V"
        resp = self.salt.cmd(self.node.id, "cmd.run", [ngx_cmd])
        if resp.get(self.node.id, ""):
            if "nginx-sticky-module-ng" in resp[self.node.id]:
                return "sticky secure httponly hash=sha1"
        return "ip_hash"

    def render_https_conf(self):
        """Copies rendered nginx virtual host config.
        """
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "cert_file": "/etc/certs/nginx.crt",
            "key_file": "/etc/certs/nginx.key",
            "oxauth_nodes": self.cluster.get_oxauth_objects(),
            "oxidp_nodes": self.cluster.get_oxidp_objects(),
            "oxtrust_nodes": self.cluster.get_oxtrust_objects(),
            "session_affinity": self.get_session_affinity(),
            "oxasimba_nodes": self.cluster.get_oxasimba_objects(),
        }

        src = "nodes/nginx/gluu_https.conf"
        dest = "/etc/nginx/sites-available/gluu_https.conf"
        self.copy_rendered_jinja_template(src, dest, ctx)

    def configure_vhost(self):
        """Enables virtual host.
        """
        rm_cmd = "rm /etc/nginx/sites-enabled/default"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [rm_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        symlink_cmd = "ln -sf /etc/nginx/sites-available/gluu_https.conf " \
                      "/etc/nginx/sites-enabled/gluu_https.conf"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [symlink_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
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
        """Restarts nginx via supervisorctl.
        """
        self.logger.info("restarting nginx")
        service_cmd = "supervisorctl restart nginx"
        self.salt.cmd(self.node.id, "cmd.run", [service_cmd])

    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]

        if not os.path.exists(self.app.config["SSL_CERT_DIR"]):
            os.makedirs(self.app.config["SSL_CERT_DIR"])

        ssl_cert = os.path.join(self.app.config["SSL_CERT_DIR"], "nginx.crt")
        ssl_key = os.path.join(self.app.config["SSL_CERT_DIR"], "nginx.key")

        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            # copy cert and key
            self.logger.info("copying existing SSL cert")
            self.salt.copy_file(self.node.id, ssl_cert, "/etc/certs/nginx.crt")
            self.logger.info("copying existing SSL key")
            self.salt.copy_file(self.node.id, ssl_key, "/etc/certs/nginx.key")
        else:
            self.gen_cert("nginx", self.cluster.decrypted_admin_pw,
                          "www-data", "www-data", hostname)

            resp = self.salt.cmd(self.node.id, "cmd.run",
                                 ["cat /etc/certs/nginx.crt"])
            if resp.get(self.node.id):
                with open(ssl_cert, "w") as fp:
                    fp.write(resp[self.node.id])

            resp = self.salt.cmd(self.node.id, "cmd.run",
                                 ["cat /etc/certs/nginx.key"])
            if resp.get(self.node.id):
                with open(ssl_key, "w") as fp:
                    fp.write(resp[self.node.id])

        self.change_cert_access("www-data", "www-data")
        self.render_https_conf()
        self.configure_vhost()
        self.copy_index_html()
        self.reconfigure_minion()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        return True

    def notify_oxtrust(self):
        """Notifies oxTrust to run required operations (if any)
        after this node has been added/removed.
        """
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
        """Post-setup callback.
        """
        if (self.provider.type == "master"
                and self.node.state == STATE_SUCCESS):
            self.notify_oxtrust()
        self.notify_oxidp()

    def teardown(self):
        """Teardowns the node.
        """
        if (self.provider.type == "master"
                and self.node.state == STATE_SUCCESS):
            self.notify_oxtrust()

        self.notify_oxidp()
        self.after_teardown()

    def copy_index_html(self):
        """Copies custom index.html for nginx.
        """
        self.logger.info("copying index.html")
        src = self.get_template_path("nodes/nginx/index.html")
        dest = "/usr/share/nginx/html/index.html"
        self.salt.copy_file(self.node.id, src, dest)

    def notify_oxidp(self):
        """Notifies oxTrust to run required operations (if any)
        after this node has been added/removed.
        """
        # a hack to avoid circular import
        from .oxidp_setup import OxidpSetup

        for oxidp in self.cluster.get_oxidp_objects():
            setup_obj = OxidpSetup(oxidp, self.cluster,
                                   self.app, logger=self.logger)

            setup_obj.delete_nginx_cert()
            setup_obj.remove_host_entries(self.node)

            # wait before telling oxidp to find nginx node
            time.sleep(2)
            setup_obj.discover_nginx()
