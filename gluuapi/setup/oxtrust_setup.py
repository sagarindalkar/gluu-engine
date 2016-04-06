# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
import time

from .base import SSLCertMixin
from .base import HostFileMixin
from .oxauth_setup import OxauthSetup
from ..database import db
from ..helper import DockerHelper


class OxtrustSetup(HostFileMixin, SSLCertMixin, OxauthSetup):
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
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": "ldap.gluu.local:{}".format(self.cluster.ldaps_port),
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
        self.docker.exec_cmd(self.node.id, "chmod +x {}".format(dest))

    def setup(self):
        """Runs the actual setup.
        """
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]

        # render config templates
        self.render_log_config_template()
        self.unpack_shib_config()
        self.copy_attribute_resolver()

        self.render_ldap_props_template()
        self.render_server_xml_template()
        self.render_oxtrust_context()
        self.write_salt_file()
        self.render_check_ssl_template()
        self.copy_tomcat_index()
        self.copy_setenv()
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

        # self.pull_oxtrust_override()
        self.add_auto_startup_entry()
        self.change_cert_access("tomcat", "tomcat")
        self.reload_supervisor()
        return True

    def teardown(self):
        """Teardowns the node.
        """
        self.notify_nginx()

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
            self.add_nginx_entry(nginx)
            self.import_nginx_cert()
        except IndexError:
            pass

    def after_setup(self):
        """Post-setup callback.
        """
        self.push_shib_certkey()
        self.discover_nginx()
        self.notify_nginx()

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        payload = """
[program:tomcat]
command=/opt/tomcat/bin/catalina.sh run
environment=CATALINA_PID=/var/run/tomcat.pid
"""

        self.logger.info("adding supervisord entry")
        cmd = '''sh -c "echo '{}' >> /etc/supervisor/conf.d/supervisord.conf"'''.format(payload)
        self.docker.exec_cmd(self.node.id, cmd)

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
        self.docker.exec_cmd(self.node.id, restart_cmd)

    def push_shib_certkey(self):
        resp = self.docker.exec_cmd(self.node.id, "cat /etc/certs/shibIDP.crt")
        crt = resp.retval

        resp = self.docker.exec_cmd(self.node.id, "cat /etc/certs/shibIDP.key")
        key = resp.retval

        for oxidp in self.cluster.get_oxidp_objects():
            # oxidp container might be in another host
            provider = db.get(oxidp.provider_id, "providers")
            docker = DockerHelper(provider, logger=self.logger)

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
                echo_cmd = '''sh -c "echo '{}' > {}"'''.format(crt, path)
                docker.exec_cmd(oxidp.id, echo_cmd)

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
                echo_cmd = '''sh -c "echo '{}' > {}"'''.format(key, path)
                docker.exec_cmd(oxidp.id, echo_cmd)

    def pull_oxtrust_override(self):
        for root, dirs, files in os.walk(self.app.config["OXTRUST_OVERRIDE_DIR"]):
            for fn in files:
                src = os.path.join(root, fn)
                dest = src.replace(self.app.config["OXTRUST_OVERRIDE_DIR"],
                                   "/opt/tomcat/webapps/identity")
                self.logger.info("copying {} to {}:{}".format(
                    src, self.node.name, dest,
                ))
                self.salt.copy_file(self.node.id, src, dest)

    def copy_setenv(self):
        src = self.get_template_path("nodes/oxtrust/setenv.sh")
        dest = "/opt/tomcat/bin/setenv.sh"
        self.logger.info("copying setenv.sh")
        self.salt.copy_file(self.node.id, src, dest)

    def render_oxtrust_context(self):
        """Renders oxTrust context file for Tomcat.
        """
        src = "nodes/oxtrust/identity.xml"
        dest = "/opt/tomcat/conf/Catalina/localhost/identity.xml"
        self.copy_rendered_jinja_template(src, dest)

    def unpack_shib_config(self):
        self.logger.info("unpacking shibboleth2 config")
        lib_dir = "/opt/tomcat/webapps/identity/WEB-INF/lib"
        jar_file = "oxtrust-configuration-2.4.3.Final.jar "
        unzip_cmd = "unzip -qq {}/{} shibboleth2/* -d /opt/tomcat/conf".format(
            lib_dir, jar_file,
        )
        self.docker.exec_cmd(self.node.id, unzip_cmd)

    def copy_attribute_resolver(self):
        src = self.get_template_path("nodes/oxtrust/attribute-resolver.xml.vm")
        dest = "/opt/tomcat/conf/shibboleth2/idp/attribute-resolver.xml.vm"
        self.logger.info("copying attribute-resolver.xml.vm")
        self.salt.copy_file(self.node.id, src, dest)
