# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os

from .base import BaseSetup
from .nginx_setup import NginxSetup


class OxBaseSetup(BaseSetup):
    def write_salt_file(self):
        """Copies salt file.
        """
        self.logger.info("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(self.cluster.passkey))

        remote_dest = os.path.join(self.node.tomcat_conf_dir, "salt")
        self.salt.copy_file(self.node.id, local_dest, remote_dest)

    def gen_keystore(self, suffix, keystore_fn, keystore_pw, in_key,
                     in_cert, user, group, hostname):
        """Generates certificates and keystore.

        :param suffix: Basename of certificate name (minus the file extension).
        :param keystore_fn: Absolute path to keystore.
        :param keystore_pw: Password for keystore.
        :param in_key: Key file as input.
        :param in_cert: Certificate file as input.
        :param user: User who owns the certificate.
        :param group: Group who owns the certificate.
        :param hostname: Name of the certificate.
        """
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
        self.docker.exec_cmd(self.node.id, export_cmd)

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
        self.docker.exec_cmd(self.node.id, import_cmd)

        self.logger.info("changing access to keystore file")
        self.docker.exec_cmd(
            self.node.id, "chown {}:{} {}".format(user, group, pkcs_fn)
        )
        self.docker.exec_cmd(self.node.id, "chmod 700 {}".format(pkcs_fn))
        self.docker.exec_cmd(
            self.node.id, "chown {}:{} {}".format(user, group, keystore_fn)
        )
        self.docker.exec_cmd(self.node.id, "chmod 700 {}".format(keystore_fn))

    def render_ldap_props_template(self):
        """Copies rendered jinja template for LDAP connection.
        """
        src = "nodes/_shared/ox-ldap.properties"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))

        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": "ldap.gluu.local:{}".format(self.cluster.ldaps_port),
            "inum_appliance": self.cluster.inum_appliance,
            "cert_folder": self.node.cert_folder,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def configure_vhost(self):
        """Configures Apache2 virtual host.
        """
        a2enmod_cmd = "a2enmod ssl headers proxy proxy_http proxy_ajp"
        self.docker.exec_cmd(self.node.id, a2enmod_cmd)

        a2dissite_cmd = "a2dissite 000-default"
        self.docker.exec_cmd(self.node.id, a2dissite_cmd)

        a2ensite_cmd = "a2ensite gluu_httpd"
        self.docker.exec_cmd(self.node.id, a2ensite_cmd)

    def notify_nginx(self):
        """Notifies nginx to re-render virtual host and restart the process.
        """
        for nginx in self.cluster.get_nginx_objects():
            setup_obj = NginxSetup(nginx, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_https_conf()
            setup_obj.restart_nginx()
