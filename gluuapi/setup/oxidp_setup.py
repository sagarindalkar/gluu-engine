# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from .oxauth_setup import OxauthSetup


class OxidpSetup(OxauthSetup):
    def copy_static_conf(self):
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
                self.get_template_path("nodes/shib/{}".format(src)),
                dest,
            )

    def render_props_template(self):
        src = "nodes/shib/oxidp-ldap.properties"
        dest = os.path.join("/opt/tomcat/conf/oxidp-ldap.properties")
        ldap_hosts = ",".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "inum_appliance": self.cluster.inum_appliance,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
            "ldap_binddn": self.node.ldap_binddn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def setup(self):
        hostname = self.node.domain_name

        # render config templates
        self.render_server_xml_template()
        self.copy_static_conf()
        self.render_props_template()
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
        for ldap in self.cluster.get_ldap_objects():
            self.import_ldap_cert(ldap)

        # copy existing oxidp config only if peer exists
        if len(self.cluster.get_oxidp_objects()):
            self.pull_shib_config()

        # add auto startup entry
        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def after_setup(self):
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

        self.notify_nginx()

    def import_ldap_cert(self, ldap):
        self.logger.info("importing ldap cert")

        cert_cmd = "echo -n | openssl s_client -connect {0}:{1} | " \
                   "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                   "> /tmp/{0}_opendj.crt".format(ldap.domain_name, ldap.ldaps_port)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [cert_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}_opendj'".format(ldap.weave_ip),
            "-file /tmp/{}_opendj.crt".format(ldap.domain_name),
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def render_nutcracker_conf(self):
        ctx = {
            "oxidp_nodes": self.cluster.get_oxidp_objects(),
        }
        self.copy_rendered_jinja_template(
            "nodes/shib/nutcracker.yml",
            "/etc/nutcracker.yml",
            ctx,
        )

    def restart_nutcracker(self):
        self.logger.info("restarting twemproxy in {}".format(self.node.name))
        restart_cmd = "supervisorctl restart nutcracker"
        self.salt.cmd(self.node.id, "cmd.run", [restart_cmd])

    def teardown(self):
        for node in self.cluster.get_oxidp_objects():
            setup_obj = OxidpSetup(node, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

        self.notify_nginx()
        self.after_teardown()

    def pull_shib_config(self):
        allowed_extensions = (".xml", ".dtd", ".config", ".xsd",)

        for root, dirs, files in os.walk("/etc/gluu/oxidp"):
            fn_list = [
                file_ for file_ in files
                if os.path.splitext(file_)[-1] in allowed_extensions
            ]

            for fn in fn_list:
                src = os.path.join(root, fn)
                dest = src.replace("/etc/gluu/oxidp", "/opt/idp")
                self.logger.info("copying {} to {}:{}".format(
                    os.path.basename(src), self.node.name, dest,
                ))
                self.salt.copy_file(self.node.id, src, dest)

    def add_auto_startup_entry(self):
        payload = """
[program:{}]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID="/var/run/tomcat.pid"

[program:memcached]
command=/usr/bin/memcached -p 11211 -u memcache -m 64 -t 4 -l 127.0.0.1 -l {}

[program:nutcracker]
command=nutcracker -c /etc/nutcracker.yml -p /var/run/nutcracker.pid -o /var/log/nutcracker.log -v 11

[program:httpd]
command=/usr/sbin/apache2ctl -DFOREGROUND
""".format(self.node.type, self.node.weave_ip)

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def render_server_xml_template(self):
        src = "nodes/shib/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_httpd_conf(self):
        src = "nodes/shib/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.node.domain_name,
            "weave_ip": self.node.weave_ip,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)
