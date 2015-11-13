# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os.path

from .base import BaseSetup
from .nginx_setup import NginxSetup


class OxauthSetup(BaseSetup):
    def write_salt_file(self):
        self.logger.info("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(self.cluster.passkey))

        remote_dest = os.path.join(self.node.tomcat_conf_dir, "salt")
        self.salt.copy_file(self.node.id, local_dest, remote_dest)

    def gen_keystore(self, suffix, keystore_fn, keystore_pw, in_key,
                     in_cert, user, group, hostname):
        self.logger.info("Creating keystore %s" % suffix)

        # Convert key to pkcs12
        pkcs_fn = '%s/%s.pkcs12' % (self.node.cert_folder, suffix)
        export_cmd = " ".join([
            'openssl', 'pkcs12', '-export',
            '-inkey', in_key,
            '-in', in_cert,
            '-out', pkcs_fn,
            '-name', hostname,
            '-passout', 'pass:%s' % keystore_pw,
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [export_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # Import p12 to keystore
        import_cmd = " ".join([
            'keytool', '-importkeystore',
            '-srckeystore', '%s/%s.pkcs12' % (self.node.cert_folder, suffix),
            '-srcstorepass', keystore_pw,
            '-srcstoretype', 'PKCS12',
            '-destkeystore', keystore_fn,
            '-deststorepass', keystore_pw,
            '-deststoretype', 'JKS',
            '-keyalg', 'RSA',
            '-noprompt',
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        self.logger.info("changing access to keystore file")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [
                ["chown {}:{} {}".format(user, group, pkcs_fn)],
                ["chmod 700 {}".format(pkcs_fn)],
                ["chown {}:{} {}".format(user, group, keystore_fn)],
                ["chmod 700 {}".format(keystore_fn)],
            ],
        )

    def render_ldap_props_template(self):
        src = "nodes/oxauth/oxauth-ldap.properties"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))

        ldap_hosts = ",".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
            "inum_appliance": self.cluster.inum_appliance,
            "cert_folder": self.node.cert_folder,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_server_xml_template(self):
        src = "nodes/oxauth/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def add_auto_startup_entry(self):
        payload = """
[program:tomcat]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID="/var/run/tomcat.pid"

[program:httpd]
command=/usr/bin/pidproxy /var/run/apache2/apache2.pid /bin/bash -c "source /etc/apache2/envvars && /usr/sbin/apache2ctl -DFOREGROUND"
"""

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def setup(self):
        hostname = self.node.domain_name

        # render config templates
        self.render_ldap_props_template()
        self.render_server_xml_template()
        self.write_salt_file()
        self.copy_duo_creds()
        self.copy_duo_web()
        self.copy_gplus_secrets()
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

        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def teardown(self):
        self.notify_nginx()
        self.after_teardown()

    def after_setup(self):
        self.notify_nginx()

    def copy_duo_creds(self):
        src = self.get_template_path("nodes/oxauth/duo_creds.json")
        dest = "/etc/certs/duo_creds.json"
        self.logger.info("copying duo_creds.json")
        self.salt.copy_file(self.node.id, src, dest)

    def copy_duo_web(self):
        src = self.get_template_path("nodes/oxauth/duo_web.py")
        dest = "/opt/tomcat/conf/python/duo_web.py"
        self.logger.info("copying duo_web.py")
        self.salt.copy_file(self.node.id, src, dest)

    def copy_gplus_secrets(self):
        src = self.get_template_path("nodes/oxauth/gplus_client_secrets.json")
        dest = "/etc/certs/gplus_client_secrets.json"
        self.logger.info("copying gplus_client_secrets.json")
        self.salt.copy_file(self.node.id, src, dest)

    def configure_vhost(self):
        a2enmod_cmd = "a2enmod ssl headers proxy proxy_http proxy_ajp"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2enmod_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        a2dissite_cmd = "a2dissite 000-default"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2dissite_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        a2ensite_cmd = "a2ensite gluu_httpd"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [a2ensite_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def render_httpd_conf(self):
        src = "nodes/oxauth/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.node.domain_name,
            "weave_ip": self.node.weave_ip,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def notify_nginx(self):
        for nginx in self.cluster.get_nginx_objects():
            setup_obj = NginxSetup(nginx, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_https_conf()
            setup_obj.restart_nginx()
