# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os

from blinker import signal

from .base import BaseSetup


class NginxSetup(BaseSetup):
    def get_session_affinity(self):
        resp = self.docker.exec_cmd(self.container.cid, "nginx -V")
        if "nginx-sticky-module-ng" in resp.retval:
            return "sticky secure httponly hash=sha1"
        return "ip_hash"

    def render_https_conf(self):
        """Copies rendered nginx virtual host config.
        """
        def resolve_weave_ip(container_id):
            return self.docker.get_container_ip(container_id)

        with self.app.app_context():
            oxauth_containers = []
            if self.cluster.count_containers("oxauth"):
                oxauth_containers.append("oxauth.weave.local")

            oxtrust_containers = []
            if self.cluster.count_containers("oxtrust"):
                oxtrust_containers.append("oxtrust.weave.local")

            ctx = {
                "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
                "cert_file": "/etc/certs/nginx.crt",
                "key_file": "/etc/certs/nginx.key",
                "session_affinity": self.get_session_affinity(),
                "oxauth_containers": oxauth_containers,
                "oxtrust_containers": oxtrust_containers,
                # "oxidp_containers": oxidp_containers,
                # "oxasimba_containers": oxasimba_containers,
            }

        src = "nginx/gluu_https.conf"
        dest = "/etc/nginx/sites-available/gluu_https.conf"
        self.copy_rendered_jinja_template(src, dest, ctx)

    def configure_vhost(self):
        """Enables virtual host.
        """
        rm_cmd = "rm /etc/nginx/sites-enabled/default"
        self.docker.exec_cmd(self.container.cid, rm_cmd)

        symlink_cmd = "ln -sf /etc/nginx/sites-available/gluu_https.conf " \
                      "/etc/nginx/sites-enabled/gluu_https.conf"
        self.docker.exec_cmd(self.container.cid, symlink_cmd)

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        payload = """
[program:{}]
command=/usr/sbin/nginx -g \\"daemon off;\\"
""".format(self.container.type)
        self.logger.debug("adding supervisord entry")
        cmd = '''sh -c "echo '{}' >> /etc/supervisor/conf.d/supervisord.conf"'''.format(payload)
        self.docker.exec_cmd(self.container.cid, cmd)

    def restart_nginx(self):
        """Restarts nginx via supervisorctl.
        """
        self.logger.debug("restarting nginx")
        service_cmd = "supervisorctl restart nginx"
        self.docker.exec_cmd(self.container.cid, service_cmd)

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
            self.logger.debug("copying existing SSL cert")
            self.docker.copy_to_container(self.container.cid, ssl_cert, "/etc/certs/nginx.crt")
            self.logger.debug("copying existing SSL key")
            self.docker.copy_to_container(self.container.cid, ssl_key, "/etc/certs/nginx.key")
        else:
            self.gen_cert("nginx", self.cluster.decrypted_admin_pw,
                          "www-data", "www-data", hostname)

            # save certs locally, so we can reuse and distribute them
            try:
                os.makedirs(self.app.config["SSL_CERT_DIR"])
            except OSError:
                pass

            resp = self.docker.exec_cmd(self.container.cid, "cat /etc/certs/nginx.crt")
            if resp.retval:
                with open(ssl_cert, "w") as fp:
                    fp.write(resp.retval)

            resp = self.docker.exec_cmd(self.container.cid, "cat /etc/certs/nginx.key")
            if resp.retval:
                with open(ssl_key, "w") as fp:
                    fp.write(resp.retval)

        self.change_cert_access("www-data", "www-data")
        self.render_https_conf()
        self.configure_vhost()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        return True

    def after_setup(self):
        """Post-setup callback.
        """
        complete_sgn = signal("nginx_setup_completed")
        complete_sgn.send(self)

    def teardown(self):
        """Teardowns the container.
        """
        complete_sgn = signal("nginx_teardown_completed")
        complete_sgn.send(self)
