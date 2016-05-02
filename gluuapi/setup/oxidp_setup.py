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
        self.render_httpd_conf()
        self.configure_vhost()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)
        self.gen_cert("httpd", self.cluster.decrypted_admin_pw,
                      "www-data", "www-data", hostname)

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
        for ldap in self.cluster.get_containers(type_="ldap"):
            self.logger.info("importing ldap cert from {}".format(ldap.hostname))

            cert_cmd = "echo -n | openssl s_client -connect {0}:{1} | " \
                       "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                       "> /etc/certs/{0}.crt".format(ldap.hostname, ldap.ldaps_port)
            cert_cmd = '''sh -c "{}"'''.format(cert_cmd)
            self.docker.exec_cmd(self.container.cid, cert_cmd)

            import_cmd = " ".join([
                "keytool -importcert -trustcacerts",
                "-alias '{}'".format(ldap.hostname),
                "-file /etc/certs/{}.crt".format(ldap.hostname),
                "-keystore {}".format(self.container.truststore_fn),
                "-storepass changeit -noprompt",
            ])
            import_cmd = '''sh -c "{}"'''.format(import_cmd)

            try:
                self.docker.exec_cmd(self.container.cid, import_cmd)
            except DockerExecError as exc:
                if exc.exit_code == 1:
                    pass

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
        self.logger.info("restarting twemproxy in {}".format(self.container.name))
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
        self.logger.info("copying {}:/opt/idp to {}:/opt/idp".format(
            oxtrust.name, self.container.name,
        ))
        self.docker.copy_to_container(
            self.container.cid, os.path.join(tmp, "idp"), "/opt",
        )

        try:
            shutil.rmtree(tmp)
        except OSError:
            pass

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        payload = """
[program:tomcat]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID=/var/run/tomcat.pid

[program:memcached]
command=/usr/bin/memcached -p 11211 -u memcache -m 64 -t 4 -l 127.0.0.1 -l {} -vv
stdout_logfile=/var/log/memcached.log
stderr_logfile=/var/log/memcached.log

[program:nutcracker]
command=nutcracker -c /etc/nutcracker.yml -p /var/run/nutcracker.pid -o /var/log/nutcracker.log -v 11

[program:httpd]
command=/usr/bin/pidproxy /var/run/apache2/apache2.pid /bin/bash -c \\"source /etc/apache2/envvars && /usr/sbin/apache2ctl -DFOREGROUND\\"
""".format(self.container.weave_ip)

        self.logger.info("adding supervisord entry")
        cmd = '''sh -c "echo '{}' >> /etc/supervisor/conf.d/supervisord.conf"'''.format(payload)
        self.docker.exec_cmd(self.container.cid, cmd)

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

    def render_httpd_conf(self):
        """Copies rendered Apache2's virtual host into the container.
        """
        src = "oxidp/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.container.hostname,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
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
            self.container.cid, "/etc/certs/shibIDP.crt", crt,
        )
        _, key = tempfile.mkstemp()
        self.docker.copy_from_container(
            self.container.cid, "/etc/certs/shibIDP.key", key,
        )

        self.docker.copy_to_container(
            self.container.cid, crt, "/etc/certs/shibIDP.crt",
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
        self.logger.info("discovering available nginx container")
        if self.cluster.count_containers(type_="nginx"):
            self.import_nginx_cert()
