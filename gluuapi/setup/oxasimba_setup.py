# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time
from glob import iglob

from .oxauth_setup import OxauthSetup


class OxasimbaSetup(OxauthSetup):
    def setup(self):
        hostname = self.node.domain_name

        # render config templates
        self.copy_selector_template()
        self.render_server_xml_template()
        self.render_httpd_conf()
        self.configure_vhost()

        # customize asimba and rebuild
        self.unpack_jar()
        self.copy_props_template()
        self.render_config_template()

        self.gen_cert("asimba", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)
        self.gen_cert("httpd", self.cluster.decrypted_admin_pw,
                      "www-data", "www-data", hostname)

        # Asimba keystore
        self.gen_keystore(
            "asimbaIDP",
            self.cluster.asimba_jks_fn,
            self.cluster.decrypted_admin_pw,
            "{}/asimba.key".format(self.node.cert_folder),
            "{}/asimba.crt".format(self.node.cert_folder),
            "tomcat",
            "tomcat",
            hostname,
        )

        # add auto startup entry
        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reconfigure_asimba()
        self.reload_supervisor()
        return True

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

    def render_server_xml_template(self):
        src = "nodes/oxasimba/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "asimba_jks_pass": self.cluster.decrypted_admin_pw,
            "asimba_jks_fn": self.cluster.asimba_jks_fn,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def render_httpd_conf(self):
        src = "nodes/oxasimba/gluu_httpd.conf"
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)

        ctx = {
            "hostname": self.node.domain_name,
            "weave_ip": self.node.weave_ip,
            "httpd_cert_fn": "/etc/certs/httpd.crt",
            "httpd_key_fn": "/etc/certs/httpd.key",
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def unpack_jar(self):
        unpack_cmd = "unzip -qq /opt/tomcat/webapps/oxasimba.war " \
                     "-d /tmp/asimba"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [unpack_cmd])
        self.salt.subscribe_event(jid, self.node.id)
        time.sleep(5)

    def copy_selector_template(self):
        src = self.get_template_path("nodes/oxasimba/asimba-selector.xml")
        dest = "{}/asimba-selector.xml".format(self.node.tomcat_conf_dir)
        self.salt.copy_file(self.node.id, src, dest)

    def copy_props_template(self):
        src = self.get_template_path("nodes/oxasimba/asimba.properties")
        dest = "/tmp/asimba/WEB-INF/asimba.properties"
        self.salt.copy_file(self.node.id, src, dest)

    def render_config_template(self):
        src = self.get_template_path("nodes/oxasimba/asimba.xml")
        dest = "/tmp/asimba/WEB-INF/conf/asimba.xml"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "asimba_jks_fn": self.cluster.asimba_jks_fn,
            "asimba_jks_pass": self.cluster.decrypted_admin_pw,
            "inum_org_fn": self.cluster.inum_org_fn,
        }
        self.render_template(src, dest, ctx)

    def reconfigure_asimba(self):
        self.logger.info("reconfiguring asimba")

        # rebuild jar
        jar_cmd = "/usr/bin/jar cmf /tmp/asimba/META-INF/MANIFEST.MF " \
                  "/tmp/asimba.war -C /tmp/asimba ."
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [jar_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # remove oxasimba.war
        rm_cmd = "rm /opt/tomcat/webapps/oxasimba.war"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [rm_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # install reconfigured asimba.jar
        mv_cmd = "mv /tmp/asimba.war /opt/tomcat/webapps/asimba.war"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [mv_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # remove temporary asimba
        rm_cmd = "rm -rf /tmp/asimba"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [rm_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def pull_idp_metadata(self):
        files = iglob("{}/metadata/*-idp-metadata.xml".format(
            self.app.config["OXIDP_VOLUMES_DIR"],
        ))

        for src in files:
            fn = os.path.basename(src)
            dest = "/opt/idp/metadata/{}".format(fn)
            self.logger.info("copying {}".format(fn))
            self.salt.copy_file(self.node.id, src, dest)

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
        self.logger.info("adding nginx entry in oxAsimba /etc/hosts file")
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
        self.logger.info("removing nginx entry in oxAsimba /etc/hosts file")
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
        self.pull_idp_metadata()
        self.discover_nginx()
        self.notify_nginx()

    def teardown(self):
        """Teardowns the node.
        """
        self.notify_nginx()
        self.after_teardown()
