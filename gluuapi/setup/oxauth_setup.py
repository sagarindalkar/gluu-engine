# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os.path

from .base import BaseSetup


class OxauthSetup(BaseSetup):
    def write_salt_file(self):
        self.logger.info("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(self.cluster.passkey))

        remote_dest = os.path.join(self.node.tomcat_conf_dir, "salt")
        self.salt.copy_file(self.node.id, local_dest, remote_dest)

    def gen_openid_keys(self):
        self.logger.info("generating OpenID key file")

        openid_key_json_fn = os.path.join(self.node.cert_folder,
                                          "oxauth-web-keys.json")
        web_inf = "/opt/tomcat/webapps/oxauth/WEB-INF"
        classpath = ":".join([
            "{}/classes".format(web_inf),
            "{}/lib/bcprov-jdk16-1.46.jar".format(web_inf),
            "{}/lib/oxauth-model-2.4.0.Final.jar".format(web_inf),
            "{}/lib/jettison-1.3.jar".format(web_inf),
            "{}/lib/commons-lang-2.6.jar".format(web_inf),
            "{}/lib/log4j-1.2.17.jar".format(web_inf),
            "{}/lib/commons-codec-1.5.jar".format(web_inf),
        ])
        key_cmd = "java -cp {} org.xdi.oxauth.util.KeyGenerator > {}".format(
            classpath, openid_key_json_fn,
        )
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [key_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        self.logger.info("changing access to OpenID key file")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [["chown {0}:{0} {1}".format("tomcat", openid_key_json_fn)],
             ["chmod 700 {}".format(openid_key_json_fn)]],
        )

    def start_tomcat(self):
        self.logger.info("starting tomcat")
        start_cmd = "export CATALINA_PID=/var/run/tomcat.pid && " \
                    "{}/bin/catalina.sh start".format(self.node.tomcat_home)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [start_cmd])
        self.salt.subscribe_event(jid, self.node.id)

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

    def render_errors_template(self):
        src = "nodes/oxauth/oxauth-errors.json"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        self.copy_rendered_jinja_template(src, dest)

    def render_config_template(self):
        src = "nodes/oxauth/oxauth-config.json"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "inum_appliance": self.cluster.inum_appliance,
            "inum_org": self.cluster.inum_org,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

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

    def render_static_conf_template(self):
        src = "nodes/oxauth/oxauth-static-conf.json"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "inum_org": self.cluster.inum_org,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_server_xml_template(self):
        src = "nodes/oxauth/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "address": self.node.weave_ip,
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def add_auto_startup_entry(self):
        # add supervisord entry
        run_cmd = "{}/bin/catalina.sh start".format(self.node.tomcat_home)
        payload = """
[program:{}]
command={}
environment=CATALINA_PID="/var/run/tomcat.pid"
""".format(self.node.type, run_cmd)

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def setup(self):
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.create_cert_dir()

        # render config templates
        # self.render_errors_template()
        # self.render_config_template()
        self.render_ldap_props_template()
        # self.render_static_conf_template()
        self.render_server_xml_template()
        self.write_salt_file()
        self.copy_duo_creds()
        self.copy_duo_web()
        self.copy_gplus_secrets()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)

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

        # self.gen_openid_keys()
        self.add_auto_startup_entry()
        self.start_tomcat()
        self.change_cert_access("tomcat", "tomcat")
        return True

    def teardown(self):
        self.after_teardown()

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
