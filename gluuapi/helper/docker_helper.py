# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json

import docker.errors
from docker import Client
from docker.tls import TLSConfig

from ..log import create_file_logger

#: Default URL to docker API
DEFAULT_DOCKER_URL = "unix:///var/run/docker.sock"


class DockerHelper(object):
    @property
    def registry_base_url(self):  # pragma: no cover
        return "registry.gluu.org:5000"

    def __init__(self, provider, logger=None):
        self.logger = logger or create_file_logger()
        self.provider = provider

        tlsconfig = None
        if self.provider.docker_base_url.startswith("https"):
            # configure TLS configuration to connect to docker
            tlsconfig = TLSConfig(
                client_cert=(self.provider.ssl_cert_path,
                             self.provider.ssl_key_path),
                verify=self.provider.ca_cert_path,
            )
        self.docker = Client(base_url=self.provider.docker_base_url,
                             tls=tlsconfig)

    def image_exists(self, name):
        """Checks whether a docker image exists.

        :param name: Image name
        :returns: ``True`` if image exists, otherwise ``False``
        """
        images = self.docker.images(name)
        return True if images else False

    def setup_container(self, name, image, env=None, port_bindings=None,
                        volumes=None, dns=None, dns_search=None):
        image = "{}/{}".format(self.registry_base_url, image)

        self.logger.info("creating container {!r}".format(name))

        # pull the image first if not exist
        if not self.image_exists(image):
            self.pull_image(image)

        return self.run_container(
            name, image, env, port_bindings, volumes, dns, dns_search,
        )

    def get_container_ip(self, container_id):
        """Gets container IP.

        :param container_id: ID or name of the container.
        :returns: Container's IP address.
        """
        info = self.docker.inspect_container(container_id)
        return info["NetworkSettings"]["IPAddress"]

    def remove_container(self, container_id):
        """Removes container.

        :param container_id: ID or name of the container.
        """
        try:
            return self.docker.remove_container(container_id, force=True)
        except docker.errors.APIError as exc:
            err_code = exc.response.status_code
            if err_code == 404:
                self.logger.warn(
                    "container {!r} does not exist".format(container_id))

    def inspect_container(self, container_id):
        """Inspects given container.

        :param container_id: ID or name of the container.
        """
        return self.docker.inspect_container(container_id)

    def stop(self, container_id):  # pragma: no cover
        # DEPRECATED; see stop_container instead
        self.stop_container(container_id)

    def stop_container(self, container_id):  # pragma: no cover
        """Stops given container.
        """
        self.docker.stop(container_id)

    def pull_image(self, image):
        resp = self.docker.pull(repository=image, stream=True)
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
                      volumes=None, dns=None, dns_search=None):
        env = env or {}
        port_bindings = port_bindings or {}
        volumes = volumes or {}
        dns = dns or []
        dns_search = dns_search or []

        container = self.docker.create_container(
            image=image,
            name=name,
            detach=True,
            environment=env,
            host_config=self.docker.create_host_config(
                port_bindings=port_bindings,
                binds=volumes,
                dns=dns,
                dns_search=dns_search,
            ),
        )
        container_id = container["Id"]
        self.logger.info("container {!r} has been created".format(name))

        if container_id:
            self.docker.start(container=container_id)
            self.logger.info("container {!r} with ID {!r} "
                             "has been started".format(name, container_id))
        return container_id
