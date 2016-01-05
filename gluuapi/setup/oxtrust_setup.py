# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time
from glob import iglob

from .oxauth_setup import OxauthSetup


class OxtrustSetup(OxauthSetup):
    def import_nginx_cert(self):
        """Imports SSL certificate from nginx node.
        """
        self.logger.info("importing nginx cert")

        # imports nginx cert into oxtrust cacerts to avoid
        # "peer not authenticated" error
        cert_cmd = "echo -n | openssl s_client -connect {}:443 | " \
                   "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                   "> /etc/certs/nginx.cert".format(self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [cert_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        der_cmd = "openssl x509 -outform der -in /etc/certs/nginx.cert -out /etc/certs/nginx.der"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [der_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(self.cluster.ox_cluster_hostname),
            "-file /etc/certs/nginx.der",
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def delete_nginx_cert(self):
        """Removes SSL cerficate of nginx node.
        """
        delete_cmd = " ".join([
            "keytool -delete",
            "-alias {}".format(self.cluster.ox_cluster_hostname),
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        self.logger.info("deleting nginx cert")
        self.salt.cmd(self.node.id, "cmd.run", [delete_cmd])

    def add_host_entries(self, nginx):
        """Adds entry into /etc/hosts file.
        """
        # currently we need to add nginx container hostname
        # to prevent "peer not authenticated" raised by oxTrust;
        # TODO: use a real DNS
        self.logger.info("adding nginx entry in oxTrust /etc/hosts file")
        # add the entry only if line is not exist in /etc/hosts
        grep_cmd = "grep -q '^{0} {1}$' /etc/hosts " \
                   "|| echo '{0} {1}' >> /etc/hosts" \
                   .format(nginx.weave_ip,
                           self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [grep_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def remove_host_entries(self, nginx):
        """Removes entry from /etc/hosts file.
        """
        # TODO: use a real DNS
        #
        # currently we need to remove nginx container hostname
        # updating ``/etc/hosts`` in-place will raise "resource or device is busy"
        # error, hence we use the following steps instead:
        #
        # 1. copy the original ``/etc/hosts``
        # 2. find-and-replace entries in copied file
        # 3. overwrite the original ``/etc/hosts``
        self.logger.info("removing nginx entry in oxTrust /etc/hosts file")
        backup_cmd = "cp /etc/hosts /tmp/hosts"
        sed_cmd = "sed -i 's/{} {}//g' /tmp/hosts && sed -i '/^$/d' /tmp/hosts".format(
            nginx.weave_ip, self.cluster.ox_cluster_hostname
        )
        overwrite_cmd = "cp /tmp/hosts /etc/hosts"
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run"],
            [[backup_cmd], [sed_cmd], [overwrite_cmd]],
        )

    def render_log_config_template(self):
        """Copies rendered oxTrust log config file.
        """
        src = "nodes/oxtrust/oxTrustLogRotationConfiguration.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "tomcat_log_folder": self.node.tomcat_log_folder,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_ldap_props_template(self):
        """Copies rendered jinja template for LDAP connection.
        """
        src = "nodes/oxtrust/oxtrust-ldap.properties"
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
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_check_ssl_template(self):
        """Renders check_ssl script into the node.
        """
        src = self.get_template_path("nodes/oxtrust/check_ssl")
        dest = "/usr/bin/{}".format(os.path.basename(src))
        ctx = {"ox_cluster_hostname": self.cluster.ox_cluster_hostname}
        self.render_template(src, dest, ctx)
        self.salt.cmd(self.node.id, "cmd.run", ["chmod +x {}".format(dest)])

    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]

        # render config templates
        self.render_log_config_template()
        self.copy_shib_config("idp")
        self.copy_shib_config("idp/schema")
        self.copy_shib_config("idp/ProfileConfiguration")
        self.copy_shib_config("idp/MetadataFilter")
        self.copy_shib_config("sp")

        self.render_ldap_props_template()
        self.render_server_xml_template()
        self.write_salt_file()
        self.render_check_ssl_template()
        self.copy_tomcat_index()
        # self.render_httpd_conf()
        # self.configure_vhost()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)
        # self.gen_cert("httpd", self.cluster.decrypted_admin_pw,
        #               "www-data", "www-data", hostname)

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

        self.reconfigure_minion()
        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def teardown(self):
        """Teardowns the node.
        """
        self.notify_nginx()
        self.after_teardown()

    def render_server_xml_template(self):
        """Copies rendered Tomcat's server.xml into the node.
        """
        src = "nodes/oxtrust/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def discover_nginx(self):
        """Discovers nginx node.
        """
        self.logger.info("discovering available nginx node")
        try:
            # if we already have nginx node in the the cluster,
            # add entry to /etc/hosts and import the cert
            nginx = self.provider.get_node_objects(type_="nginx")[0]
            self.add_host_entries(nginx)
            self.import_nginx_cert()
        except IndexError:
            pass

    def after_setup(self):
        """Post-setup callback.
        """
        self.push_shib_certkey()
        self.discover_nginx()
        self.notify_nginx()

    def copy_shib_config(self, parent_dir):
        """Copy config files located under shibboleth2 directory.
        """
        # create a generator to keep the result of globbing
        files = iglob(self.get_template_path(
            "nodes/oxtrust/shibboleth2/{}/*".format(parent_dir)
        ))

        parent_dest = "/opt/tomcat/conf/shibboleth2/{}".format(parent_dir)
        mkdir_cmd = "mkdir -p {}".format(parent_dest)
        self.salt.cmd(self.node.id, "cmd.run", [mkdir_cmd])

        for src in files:
            if os.path.isdir(src):
                continue
            fn = os.path.basename(src)
            dest = "{}/{}".format(parent_dest, fn)
            self.logger.info("copying {}".format(fn))
            self.salt.copy_file(self.node.id, src, dest)

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        payload = """
[program:tomcat]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID="/var/run/tomcat.pid"
"""

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def copy_tomcat_index(self):
        """Copies Tomcat's index.html into the node.
        """
        self.logger.info("copying index.html")
        src = self.get_template_path("nodes/oxtrust/index.html")
        dest = "/opt/tomcat/webapps/ROOT/index.html"
        self.salt.copy_file(self.node.id, src, dest)

    def restart_tomcat(self):
        """Restarts Tomcat via supervisorctl.
        """
        self.logger.info("restarting tomcat")
        restart_cmd = "supervisorctl restart tomcat"
        self.salt.cmd(self.node.id, "cmd.run", [restart_cmd])

    def push_shib_certkey(self):
        resp = self.salt.cmd(self.node.id, "cmd.run",
                             ["cat /etc/certs/shibIDP.crt"])
        crt = resp.get(self.node.id)

        resp = self.salt.cmd(self.node.id, "cmd.run",
                             ["cat /etc/certs/shibIDP.key"])
        key = resp.get(self.node.id)

        for oxidp in self.cluster.get_oxidp_objects():
            if crt:
                time.sleep(5)
                path = "/etc/certs/shibIDP.crt"
                self.logger.info(
                    "copying {0}:{1} to {2}:{1}".format(
                        self.node.name,
                        path,
                        oxidp.name,
                    )
                )
                echo_cmd = "echo '{}' > {}".format(crt, path)
                self.salt.cmd(oxidp.id, "cmd.run", [echo_cmd])

            if key:
                time.sleep(5)
                path = "/etc/certs/shibIDP.key"
                self.logger.info(
                    "copying {0}:{1} to {2}:{1}".format(
                        self.node.name,
                        path,
                        oxidp.name,
                    )
                )
                echo_cmd = "echo '{}' > {}".format(key, path)
                self.salt.cmd(oxidp.id, "cmd.run", [echo_cmd])
