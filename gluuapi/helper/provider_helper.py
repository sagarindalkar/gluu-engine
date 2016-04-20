# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

# import codecs
# import logging
# import os
# import stat

from crochet import run_in_reactor

# from .salt_helper import SaltHelper
# from .salt_helper import prepare_minion
# from .weave_helper import WeaveHelper
# from .docker_helper import DockerHelper
from ..database import db
from ..machine import Machine


@run_in_reactor
def distribute_cluster_data(filepath):
    """Distributes cluster data to all consumer providers.

    :param filepath: Path to cluster database file.
    """
    # dest = src
    # salt = SaltHelper()
    # consumer_providers = db.search_from_table(
    #     "providers", db.where("type") == "consumer"
    # )

    # for provider in consumer_providers:
    #     ping = salt.cmd(provider.hostname, "test.ping")
    #     wake up the minion (if idle)
    #     if ping.get(provider.hostname):
    #         salt.cmd(
    #             provider.hostname,
    #             "cmd.run",
    #             ["mkdir -p {}".format(os.path.dirname(dest))]
    #         )
    #         salt.copy_file(provider.hostname, src, dest)

    mc = Machine()

    # find all worker nodes where cluster database will be copied to
    worker_nodes = db.search_from_table(
        "nodes", db.where("type") == "worker",
    )
    for worker_node in worker_nodes:
        mc.scp(filepath, "{}:{}".format(worker_node.name, filepath))


class ProviderHelper(object):
    pass

    # def __init__(self, provider, app, logger=None):
    #     self.provider = provider
    #     self.cluster = db.get(provider.cluster_id, "clusters")
    #     self.app = app
    #     self.weave = WeaveHelper(provider, self.app)
    #     # self.salt = SaltHelper()
    #     self.logger = logger or logging.getLogger(
    #         __name__ + "." + self.__class__.__name__,
    #     )

    # @run_in_reactor
    # def setup(self, connect_delay=10, exec_delay=15, recover_dns=False):
    #     """Runs the actual setup.

    #     :param connect_delay: Time to wait before start connecting to minion.
    #     :param exec_delay: Time to wait before start executing remote command.
    #     """
    #     self.logger.info("Provider {} setup is started".format(self.provider.id))

    #     prepare_minion(
    #         self.provider.hostname,
    #         connect_delay=connect_delay,
    #         exec_delay=exec_delay,
    #         logger=self.logger,
    #     )
    #     self.weave.launch()
    #     self.import_docker_certs()
    #     self.docker = DockerHelper(self.provider, logger=self.logger)

    #     if recover_dns:
    #         # if weave relaunched while having containers deployed in
    #         # weave network, their DNS entries will disappear;
    #         # hence we're restoring them
    #         nodes = self.provider.get_node_objects()
    #         for node in nodes:
    #             meta = self.docker.inspect_container(node.id)
    #             if meta["State"]["Running"] is False:
    #                 continue

    #             self.weave.dns_add(node.id, node.domain_name)
    #             if node.type == "ldap":
    #                 self.weave.dns_add(node.id, "ldap.gluu.local")

    #             if node.type == "nginx":  # and self.cluster is not None:
    #                 self.weave.dns_add(node.id, self.cluster.ox_cluster_hostname)

    #     # distribute the data updates
    #     distribute_cluster_data(self.app.config["DATABASE_URI"])
    #     self.logger.info("Provider {} setup is finished".format(self.provider.id))

    # def import_docker_certs(self):
    #     """Imports certificates and keys required for accessing
    #     docker Remote API.
    #     """
    #     cert_types = {
    #         "/etc/docker/cert.pem": self.write_ssl_cert,
    #         "/etc/docker/key.pem": self.write_ssl_key,
    #         "/etc/docker/ca.pem": self.write_ca_cert,
    #     }
    #     for remote_cert_path, callback in cert_types.items():
    #         content = self.get_docker_cert(remote_cert_path)
    #         self.logger.info(
    #             "importing remote certificate {}".format(remote_cert_path)
    #         )
    #         callback(content)

    # def get_docker_cert(self, remote_cert_path):
    #     """Gets the content of certificate from remote server.

    #     :param remote_cert_path: Remote path of the certificate.
    #     """
    #     cat_cmd = "test -f {0} && cat {0}".format(remote_cert_path)
    #     resp = self.salt.cmd(self.provider.hostname, "cmd.run", [cat_cmd])

    #     try:
    #         return resp.get(self.provider.hostname, "")
    #     except AttributeError:
    #         # if provider.hostname is not a registered minion, it will
    #         # returns error string instead of a ``dict``;
    #         # calling `.get` method in string object will raise AttributeError
    #         return ""

    # def _write_cert_file(self, content, dest, filemode):
    #     """Writes a file and change the file mode.
    #     """
    #     try:
    #         os.makedirs(self.app.config["DOCKER_CERT_DIR"])
    #     except OSError as exc:
    #         # file exists
    #         if exc.errno == 17:
    #             pass
    #         else:  # pragma: no cover
    #             raise exc

    #     # temporarily set file as writable only if file exists
    #     if os.path.exists(dest):
    #         os.chmod(dest, stat.S_IWUSR)  # pragma: no cover

    #     with codecs.open(dest, mode="w", encoding="utf-8") as fp:
    #         fp.write(content)
    #         os.chmod(dest, filemode)

    # def write_ssl_cert(self, content):
    #     """Writes SSL certificate into a file and change the access.

    #     :param content: Content of the file.
    #     """
    #     # chmod 444
    #     self._write_cert_file(content, self.provider.ssl_cert_path,
    #                           stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    # def write_ssl_key(self, content):
    #     """Writes SSL key into a file and change the access.

    #     :param content: Content of the file.
    #     """
    #     # chmod 400
    #     self._write_cert_file(content, self.provider.ssl_key_path, stat.S_IRUSR)

    # def write_ca_cert(self, content):
    #     """Writes CA certificate into a file and change the access.

    #     :param content: Content of the file.
    #     """
    #     # chmod 444
    #     self._write_cert_file(content, self.provider.ca_cert_path,
    #                           stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
