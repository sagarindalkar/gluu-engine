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
import codecs
import os.path
import time

from gluuapi.setup.base import BaseSetup


class OxAuthSetup(BaseSetup):
    def gen_cert(self, suffix, password, user, hostname):
        key_with_password = "{}/{}.key.orig".format(self.node.cert_folder, suffix)
        key = "{}/{}.key".format(self.node.cert_folder, suffix)
        csr = "{}/{}.csr".format(self.node.cert_folder, suffix)
        crt = "{}/{}.crt".format(self.node.cert_folder, suffix)

        # command to create key with password file
        keypass_cmd = " ".join([
            self.node.openssl_cmd, "genrsa", "-des3",
            "-out", key_with_password,
            "-passout", "pass:{}".format(password), "2048",
        ])

        # command to create key file
        key_cmd = " ".join([
            self.node.openssl_cmd, "rsa",
            "-in", key_with_password, "-passin",
            "pass:{}".format(password),
            "-out", key,
        ])

        # command to create csr file
        csr_cmd = " ".join([
            self.node.openssl_cmd, "req", "-new",
            "-key", key,
            "-out", csr,
            "-subj", "/CN=%s/O=%s/C=%s/ST=%s/L=%s" % (
                hostname,
                self.cluster.orgName,
                self.cluster.countryCode,
                self.cluster.state,
                self.cluster.city,
            )])

        # command to create crt file
        crt_cmd = " ".join([
            self.node.openssl_cmd, "x509", "-req",
            "-days", "365",
            "-in", csr,
            "-signkey", key,
            "-out", crt,
        ])

        self.logger.info("generating certificates for {}".format(suffix))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [[keypass_cmd], [key_cmd], [csr_cmd], [crt_cmd]],
        )

        self.logger.info("changing access to {} certificates".format(suffix))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [
                ["/bin/chown {0}:{0} {1}".format(user, key_with_password)],
                ["/bin/chmod 700 {}".format(key_with_password)],
                ["/bin/chown {0}:{0} {1}".format(user, key)],
                ["/bin/chmod 700 {}".format(key)],
            ],
        )

        import_cmd = " ".join([
            "/usr/bin/keytool", "-import", "-trustcacerts",
            "-alias", "{}_{}".format(hostname, suffix),
            "-file", crt,
            "-keystore", self.node.defaultTrustStoreFN,
            "-storepass", "changeit", "-noprompt",
        ])

        self.logger.info("importing public certificate into Java truststore")
        self.salt.cmd(self.node.id, "cmd.run", [import_cmd])

    # def get_ldap_hosts(self):
    #     ldap_hosts = []
    #     for ldap_id in self.cluster.ldap_nodes:
    #         ldap = db.get(ldap_id, "nodes")
    #         if ldap:
    #             ldap_host = "{}:{}".format(ldap.local_hostname, ldap.ldaps_port)
    #             ldap_hosts.append(ldap_host)
    #     return ldap_hosts

    def write_salt_file(self):
        self.logger.info("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(self.cluster.passkey))

        remote_dest = os.path.join(self.node.tomcat_conf_dir, "salt")
        self.salt.copy_file(self.node.id, local_dest, remote_dest)

    def gen_openid_keys(self):
        openid_key_json_fn = os.path.join(self.node.cert_folder, "oxauth-web-keys.json")

        self.logger.info("generating OpenID key file")
        # waiting for oxauth.war to be unpacked
        time.sleep(2)
        web_inf = "/opt/tomcat/webapps/oxauth/WEB-INF"
        classpath = ":".join([
            "{}/classes".format(web_inf),
            "{}/lib/bcprov-jdk16-1.46.jar".format(web_inf),
            "{}/lib/oxauth-model-2.1.0.Final.jar".format(web_inf),
            "{}/lib/jettison-1.3.jar".format(web_inf),
            "{}/lib/commons-lang-2.6.jar".format(web_inf),
            "{}/lib/log4j-1.2.14.jar".format(web_inf),
            "{}/lib/commons-codec-1.5.jar".format(web_inf),
        ])
        key_cmd = "java -cp {} org.xdi.oxauth.util.KeyGenerator > {}".format(
            classpath, openid_key_json_fn,
        )
        self.salt.cmd(self.node.id, "cmd.run", [key_cmd])

        self.logger.info("changing access to OpenID key file")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [["/bin/chown {0}:{0} {1}".format("tomcat", openid_key_json_fn)],
             ["/bin/chmod 700 {}".format(openid_key_json_fn)]],
        )

    def change_cert_access(self):
        self.logger.info("changing access to {}".format(self.node.cert_folder))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [["/bin/chown -R tomcat:tomcat {}".format(self.node.cert_folder)],
             ["/bin/chmod -R 500 {}".format(self.node.cert_folder)]],
        )

    def start_tomcat(self):
        self.logger.info("starting tomcat")
        self.salt.cmd(
            self.node.id,
            "cmd.run",
            ["{}/bin/catalina.sh start".format(self.node.tomcat_home)],
        )

    def create_cert_dir(self):
        mkdir_cmd = "mkdir -p {}".format(self.node.cert_folder)
        self.salt.cmd(self.node.id, "cmd.run", [mkdir_cmd])

    def gen_keystore(self, suffix, keystore_fn, keystore_pw, in_key,
                     in_cert, user, hostname):
        self.logger.info("Creating keystore %s" % suffix)

        # Convert key to pkcs12
        pkcs_fn = '%s/%s.pkcs12' % (self.node.cert_folder, suffix)
        export_cmd = " ".join([
            self.node.openssl_cmd, 'pkcs12', '-export',
            '-inkey', in_key,
            '-in', in_cert,
            '-out', pkcs_fn,
            '-name', hostname,
            '-passout', 'pass:%s' % keystore_pw,
        ])
        self.salt.cmd(self.node.id, "cmd.run", [export_cmd])

        # Import p12 to keystore
        import_cmd = " ".join([
            self.node.keytool_cmd, '-importkeystore',
            '-srckeystore', '%s/%s.pkcs12' % (self.node.cert_folder, suffix),
            '-srcstorepass', keystore_pw,
            '-srcstoretype', 'PKCS12',
            '-destkeystore', keystore_fn,
            '-deststorepass', keystore_pw,
            '-deststoretype', 'JKS',
            '-keyalg', 'RSA',
            '-noprompt',
        ])
        self.salt.cmd(self.node.id, "cmd.run", [import_cmd])

        self.logger.info("changing access to keystore file")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [
                ["/bin/chown {0}:{0}".format(user), pkcs_fn],
                ["/bin/chmod 700 {}".format(pkcs_fn)],
                ["/bin/chown {0}:{0}".format(user), keystore_fn],
                ["/bin/chmod 700 {}".format(keystore_fn)],
            ],
        )

    def render_errors_template(self):
        src = self.node.oxauth_errors_json
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        self.render_template(src, dest)

    def render_config_template(self):
        src = self.node.oxauth_config_xml
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "hostname_oxauth_cluster": self.cluster.hostname_oxauth_cluster,
            "inumAppliance": self.cluster.inumAppliance,
            "inumOrg": self.cluster.inumOrg,
        }
        self.render_template(src, dest, ctx)

    def render_ldap_props_template(self):
        src = self.node.oxauth_ldap_properties
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ",".join(self.cluster.get_ldap_hosts()),
            "inumAppliance": self.cluster.inumAppliance,
            "certFolder": self.node.cert_folder,
        }
        self.render_template(src, dest, ctx)

    def render_static_conf_template(self):
        src = self.node.oxauth_static_conf_json
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "inumOrg": self.cluster.inumOrg,
        }
        self.render_template(src, dest, ctx)

    def render_server_xml_template(self):
        src = self.node.tomcat_server_xml
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "ip": self.node.ip,
            "shibJksPass": self.cluster.decrypted_admin_pw,
            "shibJksFn": self.cluster.shib_jks_fn,
        }
        self.render_template(src, dest, ctx)

    def render_https_conf_template(self):
        src = self.node.oxauth_https_conf
        file_basename = os.path.basename(src)
        dest = os.path.join("/etc/apache2/sites-available", file_basename)
        ctx = {
            "hostname": self.cluster.hostname_oxauth_cluster,
            "ip": self.node.ip,
            "httpdCertFn": self.node.httpd_crt,
            "httpdKeyFn": self.node.httpd_key,
            "admin_email": self.cluster.admin_email,
        }
        self.render_template(src, dest, ctx)

    def start_httpd(self):
        self.logger.info("starting httpd")
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [["a2enmod ssl headers proxy proxy_http proxy_ajp evasive"],
             ["a2dissite 000-default"],
             ["a2ensite oxauth-https"],
             ["service apache2 start"]],
        )

    def setup(self):
        start = time.time()
        self.logger.info("oxAuth setup is started")

        hostname = self.cluster.hostname_oxauth_cluster.split(":")[0]
        self.create_cert_dir()

        # render config templates
        self.render_errors_template()
        self.render_config_template()
        self.render_ldap_props_template()
        self.render_static_conf_template()
        self.render_server_xml_template()
        self.render_https_conf_template()
        self.write_salt_file()

        self.gen_cert("httpd", self.cluster.decrypted_admin_pw, "www-data", hostname)
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

        # configure tomcat to run oxauth war file
        self.start_tomcat()

        # enable sites, mods, and start httpd
        self.start_httpd()

        self.gen_openid_keys()
        self.change_cert_access()

        elapsed = time.time() - start
        self.logger.info("oxAuth setup is finished ({} seconds)".format(elapsed))
        return True
