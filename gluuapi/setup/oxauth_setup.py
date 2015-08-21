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


class OxauthSetup(BaseSetup):
    @property
    def oxauth_errors_json(self):  # pragma: no cover
        return self.get_template_path("salt/oxauth/oxauth-errors.json")

    @property
    def oxauth_ldap_properties(self):  # pragma: no cover
        return self.get_template_path("salt/oxauth/oxauth-ldap.properties")

    @property
    def oxauth_config_xml(self):  # pragma: no cover
        return self.get_template_path("salt/oxauth/oxauth-config.xml")

    @property
    def oxauth_static_conf_json(self):  # pragma: no cover
        return self.get_template_path("salt/oxauth/oxauth-static-conf.json")

    @property
    def tomcat_server_xml(self):  # pragma: no cover
        return self.get_template_path("salt/_shared/server.xml")

    @property
    def oxauth_config_marker(self):  # pragma: no cover
        return self.get_template_path("salt/oxauth/oxauth.config.reload")

    def write_salt_file(self):
        self.logger.info("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(self.cluster.passkey))

        remote_dest = os.path.join(self.node.tomcat_conf_dir, "salt")
        self.salt.copy_file(self.node.id, local_dest, remote_dest)

    def gen_openid_keys(self):
        self.logger.info("generating OpenID key file")

        unpack_cmd = "unzip -q /opt/tomcat/webapps/oxauth.war " \
                     "-d /opt/tomcat/webapps/oxauth"
        self.salt.cmd(self.node.id, "cmd.run", [unpack_cmd])

        # waiting for oxauth.war to be unpacked
        time.sleep(5)

        openid_key_json_fn = os.path.join(self.node.cert_folder, "oxauth-web-keys.json")
        web_inf = "/opt/tomcat/webapps/oxauth/WEB-INF"
        classpath = ":".join([
            "{}/classes".format(web_inf),
            "{}/lib/bcprov-jdk16-1.46.jar".format(web_inf),
            "{}/lib/oxauth-model-2.3.3.Final.jar".format(web_inf),
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
            [["chown {0}:{0} {1}".format("tomcat", openid_key_json_fn)],
             ["chmod 700 {}".format(openid_key_json_fn)]],
        )

    def start_tomcat(self):
        self.logger.info("starting tomcat")
        start_cmd = "export CATALINA_PID={0}/bin/catalina.pid && " \
                    "{0}/bin/catalina.sh start".format(self.node.tomcat_home)
        self.salt.cmd(self.node.id, "cmd.run", [start_cmd])

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
        self.salt.cmd(self.node.id, "cmd.run", [export_cmd])

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
        self.salt.cmd(self.node.id, "cmd.run", [import_cmd])

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
        src = self.oxauth_errors_json
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        self.render_template(src, dest)

    def render_config_template(self):
        src = self.oxauth_config_xml
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "inumAppliance": self.cluster.inum_appliance,
            "inumOrg": self.cluster.inum_org,
        }
        self.render_template(src, dest, ctx)

    def render_ldap_props_template(self):
        src = self.oxauth_ldap_properties
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))

        ldap_hosts = ",".join([
            "{}:{}".format(ldap.weave_ip, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
            "inumAppliance": self.cluster.inum_appliance,
            "certFolder": self.node.cert_folder,
        }
        self.render_template(src, dest, ctx)

    def render_static_conf_template(self):
        src = self.oxauth_static_conf_json
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "inumOrg": self.cluster.inum_org,
        }
        self.render_template(src, dest, ctx)

    def render_server_xml_template(self):
        src = self.tomcat_server_xml
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "address": self.node.weave_ip,
            "shibJksPass": self.cluster.decrypted_admin_pw,
            "shibJksFn": self.cluster.shib_jks_fn,
        }
        self.render_template(src, dest, ctx)

    def write_marker_file(self):
        self.logger.info("writing config marker file")
        touch_cmd = "touch {}/oxauth.config.reload".format(self.node.tomcat_conf_dir)
        self.salt.cmd(self.node.id, "cmd.run", [touch_cmd])

    def setup(self):
        hostname = self.cluster.ox_cluster_hostname.split(":")[0]
        self.create_cert_dir()

        # render config templates
        self.render_errors_template()
        self.render_config_template()
        self.render_ldap_props_template()
        self.render_static_conf_template()
        self.render_server_xml_template()
        self.write_salt_file()
        self.write_marker_file()

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

        self.gen_openid_keys()
        self.symlink_jython_lib()

        # configure tomcat to run oxauth war file
        self.start_tomcat()

        self.change_cert_access("tomcat", "tomcat")

        for ldap in self.cluster.get_ldap_objects():
            self.add_ldap_host_entry(ldap)
        return True

    def teardown(self):
        self.after_teardown()

    def add_ldap_host_entry(self, ldap):
        # for ldap in self.cluster.get_ldap_objects():
        # currently we need to add ldap container hostname
        self.logger.info("adding LDAP entry into oxAuth /etc/hosts file")
        # add the entry only if line is not exist in /etc/hosts
        grep_cmd = "grep -q '^{0} {1}$' /etc/hosts " \
                   "|| echo '{0} {1}' >> /etc/hosts" \
            .format(ldap.weave_ip, ldap.id)
        self.salt.cmd(self.node.id, "cmd.run", [grep_cmd])

    def remove_ldap_host_entry(self, ldap):
        # TODO: use a real DNS
        #
        # currently we need to remove httpd container hostname
        # updating ``/etc/hosts`` in-place will raise
        # "resource or device is busy" error, hence we use
        # the following steps instead:
        #
        # 1. copy the original ``/etc/hosts``
        # 2. find-and-replace entries in copied file
        # 3. overwrite the original ``/etc/hosts``
        self.logger.info("removing LDAP entry from oxAuth /etc/hosts file")
        backup_cmd = "cp /etc/hosts /tmp/hosts"
        sed_cmd = "sed -i 's/{} {}//g' /tmp/hosts && sed -i '/^$/d' /tmp/hosts".format(
            ldap.weave_ip, ldap.id,
        )
        overwrite_cmd = "cp /tmp/hosts /etc/hosts"
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run"],
            [[backup_cmd], [sed_cmd], [overwrite_cmd]],
        )

    def symlink_jython_lib(self):
        symlink_cmd = "ln -s /opt/jython/Lib " \
                      "/opt/tomcat/webapps/oxauth/WEB-INF/lib/Lib"
        self.salt.cmd(self.node.id, "cmd.run", [symlink_cmd])
