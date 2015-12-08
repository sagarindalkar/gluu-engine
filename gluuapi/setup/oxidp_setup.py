# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time

from .oxauth_setup import OxauthSetup


class OxidpSetup(OxauthSetup):
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

    def render_ldap_props_template(self):
        """Copies rendered jinja template for LDAP connection.
        """
        src = "nodes/oxidp/oxidp-ldap.properties"
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
        """Runs the actual setup.
        """
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]

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

        # copy existing oxidp config only if peer exists
        if len(self.cluster.get_oxidp_objects()):
            self.pull_shib_config()

        # add auto startup entry
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

        self.pull_shib_certkey()
        self.notify_nginx()
        self.discover_nginx()

    def import_ldap_certs(self):
        """Imports all LDAP certificates.
        """
        for ldap in self.cluster.get_ldap_objects():
            self.logger.info("importing ldap cert")

            cert_cmd = "echo -n | openssl s_client -connect {0}:{1} | " \
                       "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                       "> /tmp/{0}.crt".format(ldap.domain_name, ldap.ldaps_port)
            self.salt.cmd(self.node.id, "cmd.run", [cert_cmd])

            import_cmd = " ".join([
                "keytool -importcert -trustcacerts",
                "-alias '{}'".format(ldap.domain_name),
                "-file /tmp/{}.crt".format(ldap.domain_name),
                "-keystore {}".format(self.node.truststore_fn),
                "-storepass changeit -noprompt",
            ])
            self.salt.cmd(self.node.id, "cmd.run", [import_cmd])

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
        self.salt.cmd(self.node.id, "cmd.run", [restart_cmd])

    def teardown(self):
        """Teardowns the node.
        """
        for node in self.cluster.get_oxidp_objects():
            setup_obj = OxidpSetup(node, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_nutcracker_conf()
            setup_obj.restart_nutcracker()

        self.notify_nginx()
        self.after_teardown()

    def pull_shib_config(self):
        """Copies all existing oxIdp config and metadata files.
        """
        allowed_extensions = (".xml", ".dtd", ".config", ".xsd",)

        for root, dirs, files in os.walk(self.app.config["OXIDP_VOLUMES_DIR"]):
            fn_list = [
                file_ for file_ in files
                if os.path.splitext(file_)[-1] in allowed_extensions
            ]

            for fn in fn_list:
                src = os.path.join(root, fn)
                dest = src.replace(self.app.config["OXIDP_VOLUMES_DIR"],
                                   "/opt/idp")
                self.logger.info("copying {} to {}:{}".format(
                    os.path.basename(src), self.node.name, dest,
                ))
                self.salt.copy_file(self.node.id, src, dest)

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        payload = """
[program:tomcat]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID="/var/run/tomcat.pid"

[program:memcached]
command=/usr/bin/memcached -p 11211 -u memcache -m 64 -t 4 -l 127.0.0.1 -l {}

[program:nutcracker]
command=nutcracker -c /etc/nutcracker.yml -p /var/run/nutcracker.pid -o /var/log/nutcracker.log -v 11

[program:httpd]
command=/usr/bin/pidproxy /var/run/apache2/apache2.pid /bin/bash -c "source /etc/apache2/envvars && /usr/sbin/apache2ctl -DFOREGROUND"
""".format(self.node.weave_ip)

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

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
            "weave_ip": self.node.weave_ip,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def pull_shib_certkey(self):
        try:
            oxtrust = self.cluster.get_oxtrust_objects()[0]
        except IndexError:
            return

        for fn in ["shibIDP.crt", "shibIDP.key"]:
            path = "/etc/certs/{}".format(fn)
            cat_cmd = "cat {}".format(path)
            resp = self.salt.cmd(oxtrust.id, "cmd.run", [cat_cmd])

            txt = resp.get(oxtrust.id, "")
            if txt:
                time.sleep(5)
                self.logger.info(
                    "copying {0}:{1} to {2}:{1}".format(oxtrust.name, path,
                                                        self.node.name)
                )
                echo_cmd = "echo '{}' > {}".format(txt, path)
                self.salt.cmd(self.node.id, "cmd.run", [echo_cmd])

    def add_host_entries(self, nginx):
        """Adds entry into /etc/hosts file.
        """
        # currently we need to add nginx container hostname
        # to prevent "peer not authenticated" raised by oxTrust;
        # TODO: use a real DNS
        self.logger.info("adding nginx entry in oxIdp /etc/hosts file")
        # add the entry only if line is not exist in /etc/hosts
        grep_cmd = "grep -q '^{0} {1}$' /etc/hosts " \
                   "|| echo '{0} {1}' >> /etc/hosts" \
                   .format(nginx.weave_ip,
                           self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [grep_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def import_nginx_cert(self):
        """Imports SSL certificate from nginx node.
        """
        self.logger.info("importing nginx cert")

        # imports nginx cert into oxtrust cacerts to avoid
        # "peer not authenticated" error
        cert_cmd = "echo -n | openssl s_client -connect {}:443 | " \
                   "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                   "> /tmp/ox.cert".format(self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [cert_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(self.cluster.ox_cluster_hostname),
            "-file /tmp/ox.cert",
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def discover_nginx(self):
        """Discovers nginx node.
        """
        self.logger.info("discovering available nginx node")
        try:
            # if we already have nginx node in the the cluster,
            # add entry to /etc/hosts and import the cert
            nginx = self.cluster.get_nginx_objects()[0]
            self.add_host_entries(nginx)
            self.import_nginx_cert()
        except IndexError:
            pass
