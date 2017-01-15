# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from blinker import signal

from .base import OxSetup


class OxauthSetup(OxSetup):
    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        self.logger.debug("adding jetty config for supervisord")
        src = "oxauth/jetty.conf"
        dest = "/etc/supervisor/conf.d/jetty.conf"
        self.copy_rendered_jinja_template(src, dest)

        self.logger.debug("adding httpd config for supervisord")
        src = "_shared/httpd.conf"
        dest = "/etc/supervisor/conf.d/httpd.conf"
        self.copy_rendered_jinja_template(src, dest)

    def setup(self):
        hostname = self.container.hostname

        self.render_ldap_props_template()
        self.write_salt_file()
        self.render_httpd_conf()
        self.configure_vhost()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "jetty", "jetty", hostname)
        self.get_web_cert()

        self.gen_keystore(
            "shibIDP",
            self.cluster.shib_jks_fn,
            self.cluster.decrypted_admin_pw,
            "{}/shibIDP.key".format(self.container.cert_folder),
            "{}/shibIDP.crt".format(self.container.cert_folder),
            "jetty",
            "jetty",
            hostname,
        )

        self.pull_oxauth_override()
        self.add_auto_startup_entry()
        self.change_cert_access("jetty", "jetty")
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
        src = "oxauth/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.container.hostname,
            "httpd_cert_fn": "/etc/certs/nginx.crt",
            "httpd_key_fn": "/etc/certs/nginx.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def pull_oxauth_override(self):
        src = self.app.config["OXAUTH_OVERRIDE_DIR"]

        if os.path.exists(src):
            dest = "{}:/var/gluu/webapps/oxauth".format(self.node.name)
            self.logger.info("copying {} to {} recursively".format(src, dest))
            self.machine.scp(src, dest, recursive=True)
