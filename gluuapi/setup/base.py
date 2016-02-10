# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import abc
import codecs
import os.path
import shutil
import tempfile
import time

from jinja2 import Environment
from jinja2 import PackageLoader

from ..database import db
from ..log import create_file_logger
from ..helper import SaltHelper


class BaseSetup(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, node, cluster, app, logger=None):
        self.logger = logger or create_file_logger()
        self.build_dir = tempfile.mkdtemp()
        self.salt = SaltHelper()
        self.node = node
        self.cluster = cluster
        self.provider = db.get(node.provider_id, "providers")
        self.jinja_env = Environment(
            loader=PackageLoader("gluuapi", "templates")
        )
        self.app = app
        self.template_dir = self.app.config["TEMPLATES_DIR"]

    @abc.abstractmethod
    def setup(self):
        """Runs the actual setup. Must be overriden by subclass.
        """

    def after_setup(self):
        """Callback executed after ``setup`` taking place.
        """

    def remove_build_dir(self):
        """Deletes temporary build directory.
        """
        self.logger.info("removing temporary build "
                         "directory {}".format(self.build_dir))
        try:
            shutil.rmtree(self.build_dir)
        except OSError:
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

        self.logger.info("rendering {}".format(file_basename))
        self.salt.copy_file(self.node.id, local, dest)

    def gen_cert(self, suffix, password, user, group, hostname):
        """Generates certificates.

        :param suffix: Basename of certificate name (minus the file extension).
        :param password: Password used for signing the certificate.
        :param user: User who owns the certificate.
        :param group: Group who owns the certificate.
        :param hostname: Hostname used for CN (Common Name) value.
        """
        key_with_password = "{}/{}.key.orig".format(self.node.cert_folder, suffix)
        key = "{}/{}.key".format(self.node.cert_folder, suffix)
        csr = "{}/{}.csr".format(self.node.cert_folder, suffix)
        crt = "{}/{}.crt".format(self.node.cert_folder, suffix)

        self.logger.info("generating certificates for {}".format(suffix))

        # command to create key with password file
        keypass_cmd = " ".join([
            "openssl", "genrsa", "-des3",
            "-out", key_with_password,
            "-passout", "pass:'{}'".format(password), "2048",
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [keypass_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # command to create key file
        key_cmd = " ".join([
            "openssl", "rsa",
            "-in", key_with_password, "-passin",
            "pass:'{}'".format(password),
            "-out", key,
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [key_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # command to create csr file
        csr_cmd = " ".join([
            "openssl", "req", "-new",
            "-key", key,
            "-out", csr,
            "-subj", "/C=%s/ST=%s/L=%s/O=%s/CN=%s/emailAddress='%s'" % (
                self.cluster.country_code, self.cluster.state,
                self.cluster.city, self.cluster.org_name,
                self.cluster.ox_cluster_hostname,
                self.cluster.admin_email,
            )
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [csr_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        # command to create crt file
        crt_cmd = " ".join([
            "openssl", "x509", "-req",
            "-days", "365",
            "-in", csr,
            "-signkey", key,
            "-out", crt,
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [crt_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        self.logger.info("changing access to {} certificates".format(suffix))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run", "cmd.run"],
            [
                ["chown {}:{} {}".format(user, group, key_with_password)],
                ["chmod 700 {}".format(key_with_password)],
                ["chown {}:{} {}".format(user, group, key)],
                ["chmod 700 {}".format(key)],
            ],
        )

    def change_cert_access(self, user, group):
        """Modifies ownership of certificates located under predefined path.

        :param user: User who owns the certificates.
        :param group: Group who owns the certificates.
        """
        self.logger.info("changing access to {}".format(self.node.cert_folder))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [["chown -R {}:{} {}".format(user, group, self.node.cert_folder)],
             ["chmod -R 500 {}".format(self.node.cert_folder)]],
        )

    def get_template_path(self, path):
        """Gets absolute path to non-jinja template.

        :param path: Relative path to non-jinja template.
        :returns: Absolute path of non-jinja template.
        """
        template_path = os.path.join(self.template_dir, path)
        return template_path

    def teardown(self):
        """Teardown the node.
        """

    def after_teardown(self):
        """After teardown callback. This method is supposed to be called
        after calling ``teardown``.
        """
        # remove logs directory
        self.remove_build_dir()

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

        self.logger.info("rendering {}".format(file_basename))
        self.salt.copy_file(self.node.id, local, dest)

    def reload_supervisor(self):
        """Reloads supervisor.
        """
        self.logger.info("reloading supervisord; "
                         "this may take 30 seconds or more")
        reload_cmd = "kill -HUP `cat /var/run/supervisord.pid`"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [reload_cmd])
        self.salt.subscribe_event(jid, self.node.id)
        time.sleep(30)

    def reconfigure_minion(self):
        # downsizing keysize to 2048
        payload = """
keysize: 2048
"""

        self.logger.info("reconfiguring minion")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/salt/minion".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)


class SSLCertMixin(object):
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


class HostFileMixin(object):
    def add_nginx_entry(self, nginx):
        """Adds entry into /etc/hosts file.
        """
        # currently we need to add nginx container hostname
        # to prevent "peer not authenticated" raised by oxTrust;
        # TODO: use a real DNS
        self.logger.info("adding nginx entry in "
                         "{} /etc/hosts file".format(self.node.type))
        # add the entry only if line is not exist in /etc/hosts
        grep_cmd = "grep -q '^{0} {1}$' /etc/hosts " \
                   "|| echo '{0} {1}' >> /etc/hosts" \
                   .format(nginx.weave_ip,
                           self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [grep_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def remove_nginx_entry(self, nginx):
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
        self.logger.info("removing nginx entry in "
                         "{} /etc/hosts file".format(self.node.type))
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
