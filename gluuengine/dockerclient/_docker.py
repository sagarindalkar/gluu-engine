# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import os
import shutil
import tempfile
from collections import namedtuple
from contextlib import contextmanager

import docker

from ..errors import DockerExecError
from ..utils import make_tarfile
from ..utils import extract_tarfile


DockerExecResult = namedtuple("DockerExecResult",
                              ["cmd", "exit_code", "retval"])


class Docker(object):
    def __init__(self, config, swarm_config):
        self.config = config
        self.swarm_config = swarm_config
        self.registry_base_url = "gluufederation"

    def image_exists(self, name):
        """Checks whether a docker image exists.

        :param name: Image name
        :returns: ``True`` if image exists, otherwise ``False``
        """
        with self._get_client(use_swarm=False) as client:
            images = client.images(name, quiet=True)
            return True if images else False

    def setup_container(self, name, image, env=None, port_bindings=None,
                        volumes=None,
                        # dns=None,
                        # dns_search=None,
                        ulimits=None,
                        hostname=None, command=None, aliases=None):
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
            # dns=dns,
            # dns_search=dns_search,
            ulimits=ulimits,
            hostname=hostname,
            command=command,
            aliases=aliases,
        )

    # def get_container_ip(self, container_id):
    #     """Gets container IP.

    #     :param container_id: ID or name of the container.
    #     :returns: Container's IP address.
    #     """
    #     with self._get_client() as client:
    #         info = client.inspect_container(container_id)
    #         return info["NetworkSettings"]["Networks"]["weave"]["IPAddress"]

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
                except StopIteration:
                    break

            result = json.loads(output)
            if "errorDetail" in result:
                return False
            return True

    def run_container(self, name, image, env=None, port_bindings=None,
                      volumes=None,
                      # dns=None,
                      # dns_search=None,
                      ulimits=None,
                      hostname=None,
                      command=None,
                      aliases=None):
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
        # dns = dns or []
        # dns_search = dns_search or []
        ulimits = ulimits or []
        command = command or []
        aliases = aliases or []

        with self._get_client() as client:
            container = client.create_container(
                image=image,
                name=name,
                detach=True,
                environment=env,
                host_config=client.create_host_config(
                    port_bindings=port_bindings,
                    binds=volumes,
                    # dns=dns,
                    # dns_search=dns_search,
                    ulimits=ulimits,
                    # network_mode="weave",
                    # network_mode="gluunet",
                    restart_policy={
                        # "Name": "unless-stopped",
                        # "MaximumRetryCount": 10,
                        "Name": "always",
                    },
                ),
                hostname=hostname,
                command=command,
                networking_config=client.create_networking_config({
                    "gluunet": client.create_endpoint_config(
                        aliases=aliases,
                    )
                }),
            )
            container_id = container["Id"]

            if container_id:
                client.start(container=container_id)
            return container_id

    def copy_to_container(self, container, src, dest):
        res = self.exec_cmd(container, "mktemp -d")
        tmp_path = res.retval

        with make_tarfile(src) as tf:
            with self._get_client() as client:
                client.put_archive(container, tmp_path, tf)

        self.exec_cmd(
            container,
            "mkdir -p {}".format(os.path.dirname(dest)),
        )
        self.exec_cmd(
            container,
            "mv {}/{} {}".format(tmp_path, os.path.basename(src), dest),
        )
        self.exec_cmd(container, "rm -rf {}".format(tmp_path))

    def copy_from_container(self, container, src, dest):
        with tempfile.NamedTemporaryFile() as fd:
            with self._get_client() as client:
                resp, _ = client.get_archive(container, src)
                for stream in resp:
                    fd.write(stream)
                fd.seek(0)

                # pull archive to temporary path
                tmp_path = tempfile.mkdtemp()
                extract_tarfile(fd, tmp_path)

                if not os.path.exists(os.path.dirname(dest)):
                    os.makedirs(os.path.dirname(dest))
                shutil.move("{}/{}".format(tmp_path, os.path.basename(src)), dest)
                shutil.rmtree(tmp_path)

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

        client = docker.Client(base_url=cfg.get("base_url"), tls=cfg.get("tls"))
        try:
            yield client
        finally:
            client.close()
