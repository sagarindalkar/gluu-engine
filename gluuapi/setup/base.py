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
import abc
import codecs
import os.path
import shutil
import tempfile

from gluuapi.database import db
from gluuapi.log import create_file_logger
from gluuapi.helper.salt_helper import SaltHelper


class BaseSetup(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, node, cluster, logger=None, template_dir=""):
        self.logger = logger or create_file_logger()
        self.build_dir = tempfile.mkdtemp()
        self.template_dir = template_dir
        self.salt = SaltHelper()
        self.node = node
        self.cluster = cluster
        self.provider = db.get(node.provider_id, "providers")

    @abc.abstractmethod
    def setup(self):
        """Runs the actual setup. Must be overriden by subclass.
        """

    def after_setup(self):
        """Callback executed after ``setup`` taking place.
        """

    def remove_build_dir(self):
        self.logger.info("removing temporary build "
                         "directory {}".format(self.build_dir))
        shutil.rmtree(self.build_dir)

    def before_setup(self):
        """Callback executed before ``setup`` taking place.
        """

    def render_template(self, src, dest, ctx=None):
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
        key_with_password = "{}/{}.key.orig".format(self.node.cert_folder, suffix)
        key = "{}/{}.key".format(self.node.cert_folder, suffix)
        csr = "{}/{}.csr".format(self.node.cert_folder, suffix)
        crt = "{}/{}.crt".format(self.node.cert_folder, suffix)

        # command to create key with password file
        keypass_cmd = " ".join([
            "openssl", "genrsa", "-des3",
            "-out", key_with_password,
            "-passout", "pass:{}".format(password), "2048",
        ])

        # command to create key file
        key_cmd = " ".join([
            "openssl", "rsa",
            "-in", key_with_password, "-passin",
            "pass:{}".format(password),
            "-out", key,
        ])

        # command to create csr file
        csr_cmd = " ".join([
            "openssl", "req", "-new",
            "-key", key,
            "-out", csr,
            "-subj", "/CN=%s/O=%s/C=%s/ST=%s/L=%s" % (
                hostname,
                self.cluster.org_name,
                self.cluster.country_code,
                self.cluster.state,
                self.cluster.city,
            )])

        # command to create crt file
        crt_cmd = " ".join([
            "openssl", "x509", "-req",
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
                ["chown {}:{} {}".format(user, group, key_with_password)],
                ["chmod 700 {}".format(key_with_password)],
                ["chown {}:{} {}".format(user, group, key)],
                ["chmod 700 {}".format(key)],
            ],
        )

    def create_cert_dir(self):
        mkdir_cmd = "mkdir -p {}".format(self.node.cert_folder)
        self.salt.cmd(self.node.id, "cmd.run", [mkdir_cmd])

    def change_cert_access(self, user, group):
        self.logger.info("changing access to {}".format(self.node.cert_folder))
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [["chown -R {}:{} {}".format(user, group, self.node.cert_folder)],
             ["chmod -R 500 {}".format(self.node.cert_folder)]],
        )

    def get_template_path(self, path):
        template_path = os.path.join(self.template_dir, path)
        return template_path
