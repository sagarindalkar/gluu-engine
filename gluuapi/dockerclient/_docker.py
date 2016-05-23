# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import logging
from collections import namedtuple
from contextlib import contextmanager

from docker import Client

from ..errors import DockerExecError
from ..registry import REGISTRY_BASE_URL
from ..utils import po_run


DockerExecResult = namedtuple("DockerExecResult",
                              ["cmd", "exit_code", "retval"])


class Docker(object):
    def __init__(self, config, swarm_config, logger=None):
        self.config = config
        self.swarm_config = swarm_config
        self.logger = logger or logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__),
        )
        self.registry_base_url = REGISTRY_BASE_URL

    def image_exists(self, name):
        """Checks whether a docker image exists.

        :param name: Image name
        :returns: ``True`` if image exists, otherwise ``False``
        """
        with self._get_client(use_swarm=False) as client:
            images = client.images(name, quiet=True)
            return True if images else False

    def setup_container(self, name, image, env=None, port_bindings=None,
                        volumes=None, dns=None, dns_search=None, ulimits=None,
                        hostname=None):
        self.logger.info("creating container {!r}".format(name))

        image = "{}/{}".format(self.registry_base_url, image)

        # pull the image first if not exist
        if not self.image_exists(image):
            self.pull_image(image)

        return self.run_container(
            name=name,
            image=image,
            env=env,
            port_bindings=port_bindings,
            volumes=volumes,
            dns=dns,
            dns_search=dns_search,
            ulimits=ulimits,
            hostname=hostname,
        )

    # def get_container_ip(self, container_id):
    #     """Gets container IP.

    #     :param container_id: ID or name of the container.
    #     :returns: Container's IP address.
    #     """
    #     with self._get_client() as client:
    #         info = client.inspect_container(container_id)
    #         return info["NetworkSettings"]["IPAddress"]

    def remove_container(self, container_id):
        """Removes container.

        :param container_id: ID or name of the container.
        """
        with self._get_client() as client:
            return client.remove_container(container_id, force=True)

    def inspect_container(self, container_id):
        """Inspects given container.

        :param container_id: ID or name of the container.
        """
        with self._get_client() as client:
            return client.inspect_container(container_id)

    def stop_container(self, container_id):  # pragma: no cover
        """Stops given container.
        """
        with self._get_client() as client:
            client.stop(container_id)

    def pull_image(self, image):
        with self._get_client(use_swarm=False) as client:
            resp = client.pull(repository=image, stream=True)
            output = ""

            while True:
                try:
                    output = resp.next()
                    self.logger.info(output)
                except StopIteration:
                    break

            result = json.loads(output)
            if "errorDetail" in result:
                return False
            return True

    def run_container(self, name, image, env=None, port_bindings=None,
                      volumes=None, dns=None, dns_search=None,
                      ulimits=None, hostname=None):
        """Runs a docker container in detached mode.

        This is a two-steps operation:

        1. Creates container
        2. Starts container

        :param name: A name for the container.
        :param image: The image to run.
        :param env: Environment variables.
        :param port_bindings: Port bindings.
        :param volumes: Mapped volumes.
        :param dns: DNS name servers.
        :param dns_search: DNS search domains.
        :param ulimits: ulimit settings.
        :returns: A string of container ID in long format if container
                  is running successfully, otherwise an empty string.
        """
        env = env or {}
        port_bindings = port_bindings or {}
        volumes = volumes or {}
        dns = dns or []
        dns_search = dns_search or []
        ulimits = ulimits or []

        with self._get_client() as client:
            container = client.create_container(
                image=image,
                name=name,
                detach=True,
                environment=env,
                host_config=client.create_host_config(
                    port_bindings=port_bindings,
                    binds=volumes,
                    dns=dns,
                    dns_search=dns_search,
                    ulimits=ulimits,
                    network_mode="weave",
                    restart_policy={
                        "Name": "unless-stopped",
                        "MaximumRetryCount": 10,
                    },
                ),
                hostname=hostname,
            )
            container_id = container["Id"]
            self.logger.info("container {!r} has been created".format(name))

            if container_id:
                client.start(container=container_id)
                self.logger.info("container {!r} with ID {!r} "
                                 "has been started".format(name, container_id))
            return container_id

    def copy_to_container(self, container, src, dest):
        cfg_str = self._swarm_conf_str()
        cmd = "docker {} cp {} {}:{}".format(cfg_str, src, container, dest)
        stdout, stderr, err_code = po_run(cmd)
        return stdout, stderr, err_code

    def copy_from_container(self, container, src, dest):
        cfg_str = self._swarm_conf_str()
        cmd = "docker {} cp {}:{} {}".format(cfg_str, container, src, dest)
        stdout, stderr, err_code = po_run(cmd)
        return stdout, stderr, err_code

    def _swarm_conf_str(self):
        cfg_str = " ".join([
            "--tlsverify",
            "--tlscacert={}".format(self.swarm_config["tls"].ca_cert),
            "--tlscert={}".format(self.swarm_config["tls"].cert[0]),
            "--tlskey={}".format(self.swarm_config["tls"].cert[1]),
            "-H={}".format(self.swarm_config["base_url"].replace("https", "tcp")),
        ])
        return cfg_str

    def exec_cmd(self, container, cmd):
        with self._get_client() as client:
            exec_cmd = client.exec_create(container, cmd=cmd)
            retval = client.exec_start(exec_cmd)
            inspect = client.exec_inspect(exec_cmd)

            if inspect["ExitCode"] != 0:
                raise DockerExecError(
                    "error while running docker exec",
                    retval,
                    inspect["ExitCode"],
                )

            result = DockerExecResult(cmd=cmd, exit_code=inspect["ExitCode"],
                                      retval=retval.strip())
            return result

    @contextmanager
    def _get_client(self, use_swarm=True):
        if use_swarm:
            cfg = self.swarm_config
        else:
            cfg = self.config

        client = Client(base_url=cfg.get("base_url"), tls=cfg.get("tls"))
        try:
            yield client
        finally:
            client.close()
