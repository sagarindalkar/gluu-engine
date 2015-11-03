# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from .oxauth_setup import OxauthSetup


class SamlSetup(OxauthSetup):
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
        src = self.get_template_path("nodes/shib/oxTrust.properties")
        dest = os.path.join("/opt/tomcat/conf", os.path.basename(src))
        ldap_hosts = " ".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "inumAppliance": self.cluster.inum_appliance,
            "inumOrg": self.cluster.inum_org,
            "orgName": self.cluster.org_name,
            "orgShortName": self.cluster.org_short_name,
            "admin_email": self.cluster.admin_email,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "shibJksFn": self.cluster.shib_jks_fn,
            "shibJksPass": self.cluster.decrypted_admin_pw,
            "inumOrgFN": self.cluster.inum_org_fn,
            "oxTrustConfigGeneration": "enabled",
            "encoded_shib_jks_pw": self.cluster.encoded_shib_jks_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauthClient_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "inumApplianceFN": self.cluster.inum_appliance_fn,
            "truststore_fn": self.node.truststore_fn,
            "ldap_hosts": ldap_hosts,
            "ldap_binddn": self.node.ldap_binddn,
        }
        self.render_template(src, dest, ctx)

    def setup(self):
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.create_cert_dir()

        # render config templates
        self.render_server_xml_template()
        self.copy_static_conf()
        self.render_props_template()
        self.write_salt_file()

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

        self.render_memcached_conf()
        self.start_memcached()

        # copy existing saml config only if peer exists
        if len(self.cluster.get_saml_objects()):
            self.pull_shib_config()

        # add auto startup entry
        self.add_auto_startup_entry()

        self.start_tomcat()
        self.change_cert_access("tomcat", "tomcat")
        return True

    def after_setup(self):
        self.render_nutcracker_conf()
        self.start_nutcracker()

        # notify saml peers to re-render their nutcracker.yml
        # and restart the daemon
        for node in self.cluster.get_saml_objects():
            if node.id == self.node.id:
                continue

            setup_obj = SamlSetup(node, self.cluster,
                                  self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

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

    def render_memcached_conf(self):
        ctx = {"saml": self.node}
        self.copy_rendered_jinja_template(
            "nodes/shib/memcached.conf",
            "/etc/memcached.conf",
            ctx,
        )

    def start_memcached(self):
        self.logger.info("starting memcached")
        jid = self.salt.cmd_async(self.node.id, "cmd.run",
                                  ["service memcached start"])
        self.salt.subscribe_event(jid, self.node.id)

    def render_nutcracker_conf(self):
        ctx = {
            "saml_nodes": self.cluster.get_saml_objects(),
        }
        self.copy_rendered_jinja_template(
            "nodes/shib/nutcracker.yml",
            "/etc/nutcracker.yml",
            ctx,
        )

    def start_nutcracker(self):
        self.logger.info("starting twemproxy")
        start_cmd = "nutcracker -c /etc/nutcracker.yml " \
                    "-p /var/run/nutcracker.pid " \
                    "-o /var/log/nutcracker.log " \
                    "-v 11 -d"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [start_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def restart_nutcracker(self):
        self.logger.info("restarting twemproxy in {}".format(self.node.name))
        restart_cmd = "supervisorctl restart nutcracker"
        self.salt.cmd(self.node.id, "cmd.run", [restart_cmd])

    def teardown(self):
        for node in self.cluster.get_saml_objects():
            setup_obj = SamlSetup(node, self.cluster,
                                  self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()
        self.after_teardown()

    def pull_shib_config(self):
        allowed_extensions = (".xml", ".dtd", ".config", ".xsd",)

        for root, dirs, files in os.walk("/etc/gluu/saml"):
            fn_list = [
                file_ for file_ in files
                if os.path.splitext(file_)[-1] in allowed_extensions
            ]

            for fn in fn_list:
                src = os.path.join(root, fn)
                dest = src.replace("/etc/gluu/saml", "/opt/idp")
                self.logger.info("copying {} to {}:{}".format(
                    os.path.basename(src), self.node.name, dest,
                ))
                self.salt.copy_file(self.node.id, src, dest)

    def add_auto_startup_entry(self):
        # add supervisord entry
        payload = """
[program:saml]
command=/opt/tomcat/bin/catalina.sh start
environment=CATALINA_PID="/var/run/tomcat.pid"

[program:memcached]
command=service memcached start

[program:nutcracker]
command=nutcracker -c /etc/nutcracker.yml -p /var/run/nutcracker.pid -o /var/log/nutcracker.log -v 11 -d
"""

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
            "address": self.node.weave_ip,
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)
