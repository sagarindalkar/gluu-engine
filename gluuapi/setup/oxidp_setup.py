# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time

from .base import SSLCertMixin
from .base import HostFileMixin
from .oxauth_setup import OxauthSetup
from ..errors import DockerExecError
from ..database import db
from ..helper import DockerHelper


class OxidpSetup(HostFileMixin, SSLCertMixin, OxauthSetup):
    def copy_static_conf(self):
        """Copies oxIdp static configuration into the node.
        """
        static_conf = {
            "idp.xml": "/opt/tomcat/conf/Catalina/localhost/idp.xml",
            "idp-metadata.xml": "/opt/idp/metadata/idp-metadata.xml",
            "attribute-resolver.xml": "/opt/idp/conf/attribute-resolver.xml",
            "relying-party.xml": "/opt/idp/conf/relying-party.xml",
            "attribute-filter.xml": "/opt/idp/conf/attribute-filter.xml",
            "internal.xml": "/opt/idp/conf/internal.xml",
            "service.xml": "/opt/idp/conf/service.xml",
            "logging.xml": "/opt/idp/conf/logging.xml",
            "handler.xml": "/opt/idp/conf/handler.xml",
        }

        for src, dest in static_conf.items():
            self.logger.info("copying {}".format(src))
            self.salt.copy_file(
                self.node.id,
                self.get_template_path("nodes/oxidp/{}".format(src)),
                dest,
            )

    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.node.domain_name

        # render config templates
        self.render_server_xml_template()
        self.copy_static_conf()
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
            "{}/shibIDP.key".format(self.node.cert_folder),
            "{}/shibIDP.crt".format(self.node.cert_folder),
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
        for node in self.cluster.get_oxidp_objects():
            if node.id == self.node.id:
                continue

            setup_obj = OxidpSetup(node, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

        self.discover_nginx()
        self.notify_nginx()

    def import_ldap_certs(self):
        """Imports all LDAP certificates.
        """
        for ldap in self.cluster.get_ldap_objects():
            self.logger.info("importing ldap cert from {}".format(ldap.domain_name))

            cert_cmd = "echo -n | openssl s_client -connect {0}:{1} | " \
                       "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                       "> /etc/certs/{0}.crt".format(ldap.domain_name, ldap.ldaps_port)
            cert_cmd = '''sh -c "{}"'''.format(cert_cmd)
            self.docker.exec_cmd(self.node.id, cert_cmd)

            import_cmd = " ".join([
                "keytool -importcert -trustcacerts",
                "-alias '{}'".format(ldap.domain_name),
                "-file /etc/certs/{}.crt".format(ldap.domain_name),
                "-keystore {}".format(self.node.truststore_fn),
                "-storepass changeit -noprompt",
            ])
            import_cmd = '''sh -c "{}"'''.format(import_cmd)

            try:
                self.docker.exec_cmd(self.node.id, import_cmd)
            except DockerExecError as exc:
                if exc.exit_code == 1:
                    pass

    def render_nutcracker_conf(self):
        """Copies twemproxy configuration into the node.
        """
        ctx = {
            "oxidp_nodes": self.cluster.get_oxidp_objects(),
        }
        self.copy_rendered_jinja_template(
            "nodes/oxidp/nutcracker.yml",
            "/etc/nutcracker.yml",
            ctx,
        )

    def restart_nutcracker(self):
        """Restarts twemproxy via supervisorctl.
        """
        self.logger.info("restarting twemproxy in {}".format(self.node.name))
        restart_cmd = "supervisorctl restart nutcracker"
        self.docker.exec_cmd(self.node.id, restart_cmd)

    def teardown(self):
        """Teardowns the node.
        """
        for node in self.cluster.get_oxidp_objects():
            setup_obj = OxidpSetup(node, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()
        self.notify_nginx()

    def pull_shib_config(self):
        """Copies all existing oxIdp config and metadata files.
        """
        allowed_extensions = (".xml", ".dtd", ".config", ".xsd",)

        for root, dirs, files in os.walk(self.app.config["OXIDP_OVERRIDE_DIR"]):
            fn_list = [
                file_ for file_ in files
                if os.path.splitext(file_)[-1] in allowed_extensions
            ]

            for fn in fn_list:
                src = os.path.join(root, fn)
                dest = src.replace(self.app.config["OXIDP_OVERRIDE_DIR"],
                                   "/opt/idp")
                self.logger.info("copying {} to {}:{}".format(
                    src, self.node.name, dest,
                ))
                self.salt.copy_file(self.node.id, src, dest)

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
""".format(self.node.weave_ip)

        self.logger.info("adding supervisord entry")
        cmd = '''sh -c "echo '{}' >> /etc/supervisor/conf.d/supervisord.conf"'''.format(payload)
        self.docker.exec_cmd(self.node.id, cmd)

    def render_server_xml_template(self):
        """Copies rendered Tomcat's server.xml into the node.
        """
        src = "nodes/oxidp/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_httpd_conf(self):
        """Copies rendered Apache2's virtual host into the node.
        """
        src = "nodes/oxidp/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.node.domain_name,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def pull_shib_certkey(self):
        try:
            oxtrust = self.cluster.get_oxtrust_objects()[0]
        except IndexError:
            return

        # oxtrust container might be in another host
        provider = db.get(oxtrust.provider_id, "providers")
        docker = DockerHelper(provider, logger=self.logger)

        for fn in ["shibIDP.crt", "shibIDP.key"]:
            path = "/etc/certs/{}".format(fn)
            cat_cmd = "cat {}".format(path)
            resp = docker.exec_cmd(oxtrust.id, cat_cmd)

            if resp.retval:
                time.sleep(5)
                self.logger.info(
                    "copying {0}:{1} to {2}:{1}".format(oxtrust.name, path,
                                                        self.node.name)
                )
                echo_cmd = '''sh -c "echo '{}' > {}"'''.format(resp.retval, path)
                self.docker.exec_cmd(self.node.id, echo_cmd)

    def discover_nginx(self):
        """Discovers nginx node.
        """
        self.logger.info("discovering available nginx node")
        try:
            # if we already have nginx node in the the cluster,
            # add entry to /etc/hosts and import the cert
            nginx = self.cluster.get_nginx_objects()[0]
            self.add_nginx_entry(nginx)
            self.import_nginx_cert()
        except IndexError:
            pass
