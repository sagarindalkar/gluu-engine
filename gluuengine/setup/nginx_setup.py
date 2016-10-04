# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from blinker import signal

from .base import BaseSetup


class NginxSetup(BaseSetup):
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

            oxeleven_containers = []
            if self.cluster.count_containers("oxeleven"):
                oxeleven_containers.append("oxeleven.weave.local")

            ctx = {
                "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
                "cert_file": "/etc/certs/nginx.crt",
                "key_file": "/etc/certs/nginx.key",
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
        self.logger.debug("adding nginx config for supervisord")
        src = "nginx/nginx.conf"
        dest = "/etc/supervisor/conf.d/nginx.conf"
        self.copy_rendered_jinja_template(src, dest)

    def restart_nginx(self):
        """Restarts nginx via supervisorctl.
        """
        self.logger.debug("restarting nginx")
        service_cmd = "supervisorctl restart nginx"
        self.docker.exec_cmd(self.container.cid, service_cmd)

    def setup(self):
        """Runs the actual setup.
        """
        self.get_web_cert()
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
