# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from blinker import signal

from .base import OxSetup


class OxauthSetup(OxSetup):
    def setup(self):
        hostname = self.container.hostname

        self.render_ldap_props_template()
        self.write_salt_file()

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

    def pull_oxauth_override(self):
        src = self.app.config["OXAUTH_OVERRIDE_DIR"]

        if os.path.exists(src):
            dest = "{}:/var/gluu/webapps/oxauth".format(self.node.name)
            self.logger.info("copying {} to {} recursively".format(src, dest))
            self.machine.scp(src, dest, recursive=True)
