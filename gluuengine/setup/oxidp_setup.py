# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import shutil
import tempfile

from blinker import signal

from .base import OxSetup
from ..errors import DockerExecError


class OxidpSetup(OxSetup):
    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.container.hostname

        # render config templates
        self.render_server_xml_template()
        self.render_ldap_props_template()
        self.write_salt_file()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)
        self.get_web_cert()

        # IDP keystore
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

        self.import_ldap_certs()
        self.pull_shib_config()
        self.pull_shib_certkey()

        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def after_setup(self):
        """Post-setup callback.
        """
        self.render_nutcracker_conf()

        # notify oxidp peers to re-render their nutcracker.yml
        # and restart the daemon
        for container in self.cluster.get_containers(type_="oxidp"):
            if container.cid == self.container.cid:
                continue

            setup_obj = OxidpSetup(container, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

        self.discover_nginx()
        complete_sgn = signal("ox_setup_completed")
        complete_sgn.send(self)

    def import_ldap_certs(self):
        """Imports all LDAP certificates.
        """
        def import_certs(host, port):
            self.logger.debug("importing ldap cert from {}".format(host))

            cert_cmd = "echo -n | openssl s_client -connect {0}:{1} | " \
                       "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                       "> /etc/certs/{0}.crt".format(host, port)
            cert_cmd = '''sh -c "{}"'''.format(cert_cmd)
            self.docker.exec_cmd(self.container.cid, cert_cmd)

            import_cmd = " ".join([
                "keytool -importcert -trustcacerts",
                "-alias '{}'".format(host),
                "-file /etc/certs/{}.crt".format(host),
                "-keystore {}".format(self.container.truststore_fn),
                "-storepass changeit -noprompt",
            ])
            import_cmd = '''sh -c "{}"'''.format(import_cmd)

            try:
                self.docker.exec_cmd(self.container.cid, import_cmd)
            except DockerExecError as exc:
                if exc.exit_code == 1:
                    pass

        # if self.cluster.external_ldap:
        import_certs(self.cluster.external_ldap_host,
                     self.cluster.external_ldap_port)
        # else:
        #     for ldap in self.cluster.get_containers(type_="ldap"):
        #         import_certs(ldap.hostname, self.cluster.ldaps_port)

    def render_nutcracker_conf(self):
        """Copies twemproxy configuration into the container.
        """
        ctx = {
            "oxidp_containers": self.cluster.get_containers(type_="oxidp"),
        }
        self.copy_rendered_jinja_template(
            "oxidp/nutcracker.yml",
            "/etc/nutcracker.yml",
            ctx,
        )

    def restart_nutcracker(self):
        """Restarts twemproxy via supervisorctl.
        """
        self.logger.debug("restarting twemproxy in {}".format(self.container.name))
        restart_cmd = "supervisorctl restart nutcracker"
        self.docker.exec_cmd(self.container.cid, restart_cmd)

    def teardown(self):
        """Teardowns the container.
        """
        for container in self.cluster.get_containers(type_="oxidp"):
            setup_obj = OxidpSetup(container, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

        complete_sgn = signal("ox_teardown_completed")
        complete_sgn.send(self)

    def pull_shib_config(self):
        """Copies all existing oxIdp config and metadata files.
        """
        try:
            oxtrust = self.cluster.get_containers(type_="oxtrust")[0]
        except IndexError:
            oxtrust = None

        if not oxtrust:
            return

        # a placeholder for generated SAML config pulled from oxtrust container
        tmp = tempfile.mkdtemp()

        # this will put copied directory to local `<tmp>/idp` directory
        self.docker.copy_from_container(oxtrust.cid, "/opt/idp", tmp)

        # copy local `<tmp>/idp` to `/opt` inside container
        self.logger.debug("copying {}:/opt/idp to {}:/opt/idp".format(
            oxtrust.name, self.container.name,
        ))
        self.docker.copy_to_container(
            self.container.cid, os.path.join(tmp, "idp"), "/opt",
        )

        try:
            shutil.rmtree(tmp)
        except OSError:
            pass

    def render_server_xml_template(self):
        """Copies rendered Tomcat's server.xml into the container.
        """
        src = "oxidp/server.xml"
        dest = os.path.join(self.container.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def pull_shib_certkey(self):
        try:
            oxtrust = self.cluster.get_containers(type_="oxtrust")[0]
        except IndexError:
            oxtrust = None

        if not oxtrust:
            return

        _, crt = tempfile.mkstemp()
        self.docker.copy_from_container(
            oxtrust.cid, "/etc/certs/shibIDP.crt", crt,
        )

        _, key = tempfile.mkstemp()
        self.docker.copy_from_container(
            oxtrust.cid, "/etc/certs/shibIDP.key", key,
        )

        self.logger.debug(
            "copying {}:/etc/certs/shibIDP.crt "
            "to {}:/etc/certs/shibIDP.crt".format(
                oxtrust.cid, self.container.cid
            )
        )

        self.docker.copy_to_container(
            self.container.cid, crt, "/etc/certs/shibIDP.crt",
        )

        self.logger.debug(
            "copying {}:/etc/certs/shibIDP.key "
            "to {}:/etc/certs/shibIDP.key".format(
                oxtrust.cid, self.container.cid
            )
        )

        self.docker.copy_to_container(
            self.container.cid, key, "/etc/certs/shibIDP.key",
        )

        for fn in (crt, key,):
            try:
                os.unlink(fn)
            except OSError:
                pass

    def discover_nginx(self):
        """Discovers nginx node.
        """
        self.logger.debug("discovering available nginx container")
        if self.cluster.count_containers(type_="nginx"):
            self.import_nginx_cert()
