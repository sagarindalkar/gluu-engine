# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from blinker import signal

from .base import OxSetup


class OxelevenSetup(OxSetup):
    def render_server_xml_template(self):
        """Copies rendered Tomcat's server.xml into the container.
        """
        src = "oxeleven/server.xml"
        dest = os.path.join(self.container.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        self.logger.debug("adding tomcat config for supervisord")
        src = "_shared/tomcat.conf"
        dest = "/etc/supervisor/conf.d/tomcat.conf"
        self.copy_rendered_jinja_template(src, dest)

        self.logger.debug("adding httpd config for supervisord")
        src = "_shared/httpd.conf"
        dest = "/etc/supervisor/conf.d/httpd.conf"
        self.copy_rendered_jinja_template(src, dest)

    def setup(self):
        hostname = self.container.hostname

        # render config templates
        self.render_server_xml_template()
        self.write_salt_file()
        self.render_httpd_conf()
        self.configure_vhost()
        self.copy_oxeleven_config()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)
        self.get_web_cert()

        self.gen_keystore(
            "shibIDP",
            self.cluster.shib_jks_fn,
            self.cluster.decrypted_admin_pw,
            "{}/shibIDP.key".format(self.container.cert_folder),
            "{}/shibIDP.crt".format(self.container.cert_folder),
            "tomcat",
            "tomcat",
            hostname,
        )

        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def teardown(self):
        """Teardowns the container.
        """
        complete_sgn = signal("ox_teardown_completed")
        complete_sgn.send(self)

    def after_setup(self):
        """Post-setup callback.
        """
        complete_sgn = signal("ox_setup_completed")
        complete_sgn.send(self)

    def render_httpd_conf(self):
        """Copies rendered Apache2's virtual host into the container.
        """
        src = "oxeleven/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.container.hostname,
            "httpd_cert_fn": "/etc/certs/nginx.crt",
            "httpd_key_fn": "/etc/certs/nginx.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def copy_oxeleven_config(self):
        src = "oxeleven/oxeleven-config.json"
        file_basename = os.path.basename(src)
        dest = os.path.join("/opt/tomcat/conf", file_basename)
        self.copy_rendered_jinja_template(src, dest)
