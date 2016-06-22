# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os.path
import shutil
import tempfile
import time

from jinja2 import Environment
from jinja2 import PackageLoader

from ..database import db
from ..log import create_file_logger
from ..errors import DockerExecError
from ..machine import Machine
from ..dockerclient import Docker
from ..weave import Weave


class BaseSetup(object):
    supervisor_reload_delay = 10

    def __init__(self, container, cluster, app, logger=None):
        self.logger = logger or create_file_logger()
        self.app = app
        self.build_dir = tempfile.mkdtemp()
        self.container = container
        with self.app.app_context():
            self.node = db.get(self.container.node_id, "nodes")
        self.cluster = cluster
        self.jinja_env = Environment(
            loader=PackageLoader("gluuengine", "templates")
        )
        self.template_dir = self.app.config["TEMPLATES_DIR"]
        self.machine = Machine()

        with self.app.app_context():
            try:
                master_node = db.search_from_table(
                    "nodes", {"type": "master"},
                )[0]
            except IndexError:  # pragma: no cover
                master_node = self.node

        self.docker = Docker(
            self.machine.config(self.node.name),
            self.machine.swarm_config(master_node.name),
        )

    def setup(self):  # pragma: no cover
        """Runs the actual setup. Must be overriden by subclass.
        """
        raise NotImplementedError("setup method must be overriden")

    def after_setup(self):
        """Callback executed after ``setup`` taking place.
        """

    def remove_build_dir(self):
        """Deletes temporary build directory.
        """
        self.logger.debug("removing temporary build "
                          "directory {}".format(self.build_dir))
        try:
            shutil.rmtree(self.build_dir)
        except OSError:  # pragma: no cover
            pass

    def render_template(self, src, dest, ctx=None):
        """Renders non-jinja template.

        :param src: Relative path to template.
        :param ctx: Context that will be populated into template.
        :returns: String of rendered template.
        """
        ctx = ctx or {}
        file_basename = os.path.basename(src)
        local = os.path.join(self.build_dir, file_basename)

        with codecs.open(src, "r", encoding="utf-8") as fp:
            rendered_content = fp.read() % ctx

        with codecs.open(local, "w", encoding="utf-8") as fp:
            fp.write(rendered_content)

        self.logger.debug("rendering {}".format(file_basename))
        self.docker.copy_to_container(self.container.cid, local, dest)

    def gen_cert(self, suffix, password, user, group, hostname):
        """Generates certificates.

        :param suffix: Basename of certificate name (minus the file extension).
        :param password: Password used for signing the certificate.
        :param user: User who owns the certificate.
        :param group: Group who owns the certificate.
        :param hostname: Hostname used for CN (Common Name) value.
        """
        self.logger.debug("generating certificates for {}".format(suffix))
        key_with_password = "{}/{}.key.orig".format(self.container.cert_folder, suffix)
        key = "{}/{}.key".format(self.container.cert_folder, suffix)
        csr = "{}/{}.csr".format(self.container.cert_folder, suffix)
        crt = "{}/{}.crt".format(self.container.cert_folder, suffix)

        # command to create key with password file
        keypass_cmd = " ".join([
            "openssl", "genrsa", "-des3",
            "-out", key_with_password,
            "-passout", "pass:'{}'".format(password), "2048",
        ])
        keypass_cmd = '''sh -c "{}"'''.format(keypass_cmd)
        self.docker.exec_cmd(self.container.cid, keypass_cmd)

        # command to create key file
        key_cmd = " ".join([
            "openssl", "rsa",
            "-in", key_with_password, "-passin",
            "pass:'{}'".format(password),
            "-out", key,
        ])
        key_cmd = '''sh -c "{}"'''.format(key_cmd)
        self.docker.exec_cmd(self.container.cid, key_cmd)

        # command to create csr file
        csr_cmd = " ".join([
            "openssl", "req", "-new",
            "-key", key,
            "-out", csr,
            "-subj", "/C='%s'/ST='%s'/L='%s'/O='%s'/CN='%s'/emailAddress='%s'" % (
                self.cluster.country_code,
                self.cluster.state,
                self.cluster.city,
                self.cluster.org_name,
                hostname,
                self.cluster.admin_email,
            )
        ])
        csr_cmd = '''sh -c "{}"'''.format(csr_cmd)
        self.docker.exec_cmd(self.container.cid, csr_cmd)

        # command to create crt file
        crt_cmd = " ".join([
            "openssl", "x509", "-req",
            "-days", "365",
            "-in", csr,
            "-signkey", key,
            "-out", crt,
        ])
        crt_cmd = '''sh -c "{}"'''.format(crt_cmd)
        self.docker.exec_cmd(self.container.cid, crt_cmd)

        self.logger.debug("changing access to {} certificates".format(suffix))
        self.docker.exec_cmd(
            self.container.cid,
            "chown {}:{} {}".format(user, group, key_with_password),
        )
        self.docker.exec_cmd(
            self.container.cid,
            "chmod 700 {}".format(key_with_password),
        )
        self.docker.exec_cmd(
            self.container.cid,
            "chown {}:{} {}".format(user, group, key),
        )
        self.docker.exec_cmd(
            self.container.cid,
            "chmod 700 {}".format(key),
        )

    def change_cert_access(self, user, group):
        """Modifies ownership of certificates located under predefined path.

        :param user: User who owns the certificates.
        :param group: Group who owns the certificates.
        """
        self.logger.debug("changing access to {}".format(self.container.cert_folder))
        self.docker.exec_cmd(
            self.container.cid,
            "chown -R {}:{} {}".format(user, group, self.container.cert_folder),
        )
        self.docker.exec_cmd(
            self.container.cid,
            "chmod -R 500 {}".format(self.container.cert_folder),
        )

    def get_template_path(self, path):
        """Gets absolute path to non-jinja template.

        :param path: Relative path to non-jinja template.
        :returns: Absolute path of non-jinja template.
        """
        template_path = os.path.join(self.template_dir, path)
        return template_path

    def teardown(self):
        """Teardown the container.
        """

    def after_teardown(self):
        """After teardown callback. This method is supposed to be called
        after calling ``teardown``.
        """

    def render_jinja_template(self, src, ctx=None):
        """Renders jinja template.

        :param src: Relative path to template.
        :param ctx: Context that will be populated into template.
        :returns: String of rendered template.
        """
        ctx = ctx or {}
        template = self.jinja_env.get_template(src)
        return template.render(**ctx)

    def copy_rendered_jinja_template(self, src, dest, ctx=None):
        """Copies rendered template to minion.

        :param src: Relative path to template.
        :param dest: Destination path in minion.
        :param ctx: Context that will be populated into template.
        """
        rendered_content = self.render_jinja_template(src, ctx)
        file_basename = os.path.basename(src)
        local = os.path.join(self.build_dir, file_basename)

        with codecs.open(local, "w", encoding="utf-8") as fp:
            fp.write(rendered_content)

        self.logger.debug("rendering {}".format(file_basename))
        self.docker.copy_to_container(self.container.cid, local, dest)

    def reload_supervisor(self):
        """Reloads supervisor.
        """
        self.logger.info(
            "reloading supervisord; this may take "
            "{} seconds or more".format(self.supervisor_reload_delay)
        )
        self.docker.exec_cmd(self.container.cid, "supervisorctl reload")
        time.sleep(self.supervisor_reload_delay)

    def ldap_failover_hostname(self):
        return self.ldap_host

    @property
    def ldap_binddn(self):
        if self.cluster.external_ldap:
            return self.cluster.external_ldap_binddn
        return self.cluster.ldap_binddn

    @property
    def encoded_ox_ldap_pw(self):
        if self.cluster.external_ldap:
            return self.cluster.external_ldap_encoded_password
        return self.cluster.encoded_ox_ldap_pw

    @property
    def inum_appliance(self):
        if self.cluster.external_ldap:
            return self.cluster.external_ldap_inum_appliance
        return self.cluster.inum_appliance

    @property
    def ldap_host(self):
        # get hostname for ldap failover
        if self.cluster.external_ldap:
            hostname = self.cluster.external_ldap_host
        else:
            weave = Weave(self.node, self.app)
            _, dns_search = weave.dns_args()
            hostname = "ldap.{}".format(dns_search.rstrip("."))
        return hostname


class OxSetup(BaseSetup):
    def write_salt_file(self):
        """Copies salt file.
        """
        if self.cluster.external_ldap:
            salt = self.cluster.external_encoded_salt
        else:
            salt = self.cluster.passkey

        self.logger.debug("writing salt file")

        local_dest = os.path.join(self.build_dir, "salt")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write("encodeSalt = {}".format(salt))

        remote_dest = os.path.join(self.container.tomcat_conf_dir, "salt")
        self.docker.copy_to_container(self.container.cid, local_dest, remote_dest)

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
        self.logger.debug("Creating keystore %s" % suffix)

        # Convert key to pkcs12
        pkcs_fn = '%s/%s.pkcs12' % (self.container.cert_folder, suffix)
        export_cmd = " ".join([
            'openssl', 'pkcs12', '-export',
            '-inkey', in_key,
            '-in', in_cert,
            '-out', pkcs_fn,
            '-name', hostname,
            '-passout', 'pass:%s' % keystore_pw,
        ])
        self.docker.exec_cmd(self.container.cid, export_cmd)

        # Import p12 to keystore
        import_cmd = " ".join([
            'keytool', '-importkeystore',
            '-srckeystore', '%s/%s.pkcs12' % (self.container.cert_folder, suffix),
            '-srcstorepass', keystore_pw,
            '-srcstoretype', 'PKCS12',
            '-destkeystore', keystore_fn,
            '-deststorepass', keystore_pw,
            '-deststoretype', 'JKS',
            '-keyalg', 'RSA',
            '-noprompt',
        ])
        self.docker.exec_cmd(self.container.cid, import_cmd)

        self.logger.debug("changing access to keystore file")
        self.docker.exec_cmd(
            self.container.cid, "chown {}:{} {}".format(user, group, pkcs_fn)
        )
        self.docker.exec_cmd(self.container.cid, "chmod 700 {}".format(pkcs_fn))
        self.docker.exec_cmd(
            self.container.cid, "chown {}:{} {}".format(user, group, keystore_fn)
        )
        self.docker.exec_cmd(self.container.cid, "chmod 700 {}".format(keystore_fn))

    def render_ldap_props_template(self):
        """Copies rendered jinja template for LDAP connection.
        """

        src = "_shared/ox-ldap.properties"
        dest = os.path.join(self.container.tomcat_conf_dir, os.path.basename(src))

        ctx = {
            "ldap_binddn": self.ldap_binddn,
            "encoded_ox_ldap_pw": self.encoded_ox_ldap_pw,
            "ldap_hosts": "{}:{}".format(self.ldap_failover_hostname(), self.cluster.ldaps_port),
            "inum_appliance": self.inum_appliance,
            "cert_folder": self.container.cert_folder,
        }
        self.copy_rendered_jinja_template(src, dest, ctx)

    def configure_vhost(self):
        """Configures Apache2 virtual host.
        """
        a2enmod_cmd = "a2enmod ssl headers proxy proxy_http proxy_ajp"
        self.docker.exec_cmd(self.container.cid, a2enmod_cmd)

        a2dissite_cmd = "a2dissite 000-default"
        self.docker.exec_cmd(self.container.cid, a2dissite_cmd)

        a2ensite_cmd = "a2ensite gluu_httpd"
        self.docker.exec_cmd(self.container.cid, a2ensite_cmd)

    def import_nginx_cert(self):
        """Imports SSL certificate from nginx container.
        """
        self.logger.debug("importing nginx cert to {}".format(self.container.name))

        # imports nginx cert into oxtrust cacerts to avoid
        # "peer not authenticated" error
        ssl_cert = os.path.join(self.app.config["SSL_CERT_DIR"], "nginx.crt")
        self.docker.copy_to_container(self.container.cid, ssl_cert, "/etc/certs/nginx.crt")

        der_cmd = "openssl x509 -outform der -in /etc/certs/nginx.crt -out /etc/certs/nginx.der"
        self.docker.exec_cmd(self.container.cid, der_cmd)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(self.cluster.ox_cluster_hostname),
            "-file /etc/certs/nginx.der",
            "-keystore {}".format(self.container.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        import_cmd = '''sh -c "{}"'''.format(import_cmd)

        try:
            self.docker.exec_cmd(self.container.cid, import_cmd)
        except DockerExecError as exc:  # pragma: no cover
            if exc.exit_code == 1:
                # certificate already imported
                pass
