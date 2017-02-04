# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import tempfile
import os

from blinker import signal

from .base import OxSetup


class OxtrustSetup(OxSetup):
    def render_check_ssl_template(self):
        """Renders check_ssl script into the container.
        """
        src = self.get_template_path("oxtrust/check_ssl")
        dest = "/usr/bin/{}".format(os.path.basename(src))
        ctx = {"ox_cluster_hostname": self.cluster.ox_cluster_hostname}
        self.render_template(src, dest, ctx)
        self.docker.exec_cmd(self.container.cid, "chmod +x {}".format(dest))

    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]

        self.render_ldap_props_template()
        self.write_salt_file()
        self.render_check_ssl_template()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "jetty", "jetty", hostname)
        self.get_web_cert()

        # IDP keystore
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

        self.pull_oxtrust_override()
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
        self.push_shib_certkey()
        self.discover_nginx()
        complete_sgn = signal("ox_setup_completed")
        complete_sgn.send(self)

    def push_shib_certkey(self):
        _, crt = tempfile.mkstemp()
        self.docker.copy_from_container(
            self.container.cid, "/etc/certs/shibIDP.crt", crt,
        )
        _, key = tempfile.mkstemp()
        self.docker.copy_from_container(
            self.container.cid, "/etc/certs/shibIDP.key", key,
        )

        for oxidp in self.cluster.get_containers(type_="oxidp"):
            self.docker.copy_to_container(
                oxidp.cid, crt, "/etc/certs/shibIDP.crt",
            )
            self.docker.copy_to_container(
                oxidp.cid, key, "/etc/certs/shibIDP.key",
            )

        for fn in (crt, key,):
            try:
                os.unlink(fn)
            except OSError:
                pass

    def pull_oxtrust_override(self):
        src = self.app.config["OXTRUST_OVERRIDE_DIR"]

        if os.path.exists(src):
            dest = "{}:/var/gluu/webapps/oxtrust".format(self.node.name)
            self.logger.info("copying {} to {} recursively".format(src, dest))
            self.machine.scp(src, dest, recursive=True)
