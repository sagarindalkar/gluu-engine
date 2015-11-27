# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import abc
import codecs
import os.path
import shutil
import tempfile

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
            "-subj", "'/CN=%s/O=%s/C=%s/ST=%s/L=%s'" % (
                hostname,
                self.cluster.org_name,
                self.cluster.country_code,
                self.cluster.state,
                self.cluster.city,
            )])
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
        reload_cmd = "kill -HUP `cat /var/run/supervisord.pid`"
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [reload_cmd])
        self.salt.subscribe_event(jid, self.node.id)
