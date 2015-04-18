# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os.path
import time

from api.setup.oxauth_setup import OxAuthSetup
from api.database import db


class OxTrustSetup(OxAuthSetup):
    def import_oxauth_cert(self):
        # imports oxauth cert into oxtrust cacerts to avoid "peer not authenticated" error
        cert_cmd = "echo -n | openssl s_client -connect {} | " \
                   "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                   "> /tmp/oxauth.cert".format(self.cluster.hostname_oxauth_cluster)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(self.cluster.hostname_oxauth_cluster),
            "-file /tmp/oxauth.cert",
            "-keystore {}".format(self.node.defaultTrustStoreFN),
            "-storepass changeit -noprompt",
        ])
        self.saltlocal.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [[cert_cmd], [import_cmd]]
        )

    def update_host_entries(self):
        self.logger.info("updating host entries in /etc/hosts")
        for oxauth_id in self.cluster.oxauth_nodes:
            oxauth = db.get(oxauth_id, "nodes")

            if not oxauth:
                continue

            self.saltlocal.cmd(
                self.node.id,
                "cmd.run",
                ["echo '{} {}' >> /etc/hosts".format(
                    oxauth.ip,
                    self.cluster.hostname_oxauth_cluster.split(":")[0],
                )],
            )

    def render_cache_props_template(self):
        src = self.node.oxtrust_cache_refresh_properties
        dest_dir = os.path.join(self.node.tomcat_conf_dir, "template", "conf")
        dest = os.path.join(dest_dir, os.path.basename(src))
        self.saltlocal.cmd(self.node.id, "cmd.run",
                           ["mkdir -p {}".format(dest_dir)])
        self.render_template(src, dest)

    def render_log_config_template(self):
        src = self.node.oxtrust_log_rotation_configuration
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "tomcat_log_folder": self.node.tomcat_log_folder,
        }
        self.render_template(src, dest, ctx)

    def render_props_template(self):
        src = self.node.oxtrust_properties
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "inumAppliance": self.cluster.inumAppliance,
            "inumOrg": self.cluster.inumOrg,
            "orgName": self.cluster.orgName,
            "orgShortName": self.cluster.orgShortName,
            "admin_email": self.cluster.admin_email,
            "hostname_oxtrust_cluster": self.cluster.hostname_oxtrust_cluster,
            "shibJksFn": self.cluster.shib_jks_fn,
            "shibJksPass": self.cluster.decrypted_admin_pw,
            "inumOrgFN": self.cluster.inumOrgFN,
            "oxTrustConfigGeneration": self.node.oxtrust_config_generation,
            "encoded_shib_jks_pw": self.cluster.encoded_shib_jks_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "hostname_oxauth_cluster": self.cluster.hostname_oxauth_cluster,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauthClient_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "inumApplianceFN": self.cluster.inumApplianceFN,
        }
        self.render_template(src, dest, ctx)

    def render_ldap_props_template(self):
        src = self.node.oxtrust_ldap_properties
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ",".join(self.get_ldap_hosts()),
            "inumAppliance": self.cluster.inumAppliance,
        }
        self.render_template(src, dest, ctx)

    def setup(self):
        start = time.time()
        self.logger.info("oxTrust setup is started")

        # update host entries
        self.update_host_entries()

        # render config templates
        self.render_cache_props_template()
        self.render_log_config_template()
        self.render_props_template()
        self.render_ldap_props_template()
        self.render_server_xml_template()
        self.write_salt_file()

        # Create or copy key material to /etc/certs
        self.create_cert_dir()

        hostname = self.cluster.hostname_oxtrust_cluster.split(":")[0]
        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw, "tomcat", hostname)

        # IDP keystore
        self.gen_keystore(
            "shibIDP",
            self.cluster.shib_jks_fn,
            self.cluster.decrypted_admin_pw,
            "{}/shibIDP.key".format(self.node.cert_folder),
            "{}/shibIDP.crt".format(self.node.cert_folder),
            "tomcat",
            hostname,
        )
        self.import_oxauth_cert()

        # Configure tomcat to run oxtrust war file
        # FIXME: cannot found "facter" and "check_ssl" commands
        self.start_tomcat()

        self.change_cert_access()

        elapsed = time.time() - start
        self.logger.info("oxTrust setup is finished ({} seconds)".format(elapsed))
        return True
