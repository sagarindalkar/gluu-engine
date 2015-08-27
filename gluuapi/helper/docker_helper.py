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
import json
import os.path
import tempfile
import shutil

import docker.errors
import requests
from docker import Client
from docker.tls import TLSConfig
from docker.errors import TLSParameterError
from docker.utils import create_host_config

from gluuapi.log import create_file_logger

#: Default URL to docker API
DEFAULT_DOCKER_URL = "unix:///var/run/docker.sock"


class DockerHelper(object):
    def __init__(self, provider, logger=None):
        self.logger = logger or create_file_logger()
        self.docker = None
        self.provider = provider
        self.connect()

    def connect(self):
        if not self.docker:
            tlsconfig = None
            if self.provider.docker_base_url.startswith("https"):
                try:
                    # configure TLS configuration to connect to docker
                    tlsconfig = TLSConfig(
                        client_cert=(self.provider.ssl_cert_path,
                                     self.provider.ssl_key_path),
                        verify=self.provider.ca_cert_path,
                    )
                except TLSParameterError as exc:
                    self.logger.warn(exc)

            self.docker = Client(base_url=self.provider.docker_base_url,
                                 tls=tlsconfig)

    def image_exists(self, name):
        """Checks whether a docker image exists.

        :param name: Image name
        :returns: ``True`` if image exists, otherwise ``False``
        """
        images = self.docker.images(name)
        return True if images else False

    def build_image(self, path, tag):
        """Builds a docker image.

        :param path: Path to a directory where ``Dockerfile`` is located.
        :param tag: Desired tag name.
        :returns: ``True`` if image successfully built, otherwise ``False``
        """
        self.logger.info("building {} image".format(tag))

        # pulling image update from Registry V2 raises error,
        # hence we skip the updates until we have a correct implementation
        pull = False
        resp = self.docker.build(path, tag=tag, quiet=True, rm=True,
                                 forcerm=True, pull=pull)

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

    def run_container(self, name, image, port_bindings=None):
        """Runs a docker container in detached mode.

        This is a two-steps operation:

        1. Creates container
        2. Starts container

        :param name: Desired container name.
        :param image: Existing image name.
        :returns: A string of container ID in long format if container
                is running successfully, otherwise an empty string.
        """
        port_bindings = port_bindings or {}
        container_id = ""

        self.logger.info("creating container {!r}".format(name))
        env = {
            "SALT_MASTER_IPADDR": os.environ.get("SALT_MASTER_IPADDR"),
        }
        container = self.docker.create_container(
            image=image, name=name, detach=True, environment=env,
            host_config=create_host_config(port_bindings=port_bindings),
        )
        container_id = container["Id"]
        self.logger.info("container {!r} has been created".format(name))

        if container_id:
            self.docker.start(container=container_id)
            self.logger.info("container {!r} with ID {!r} "
                             "has been started".format(name, container_id))
        return container_id

    def get_remote_files(self, *files):
        """Retrieves files from remote paths.

        All retrieved files will be stored under a same temporary directory.

        :param files: List of files.
        :returns: Absolute path to temporary directory where all files
                were downloaded to.
        """
        local_dir = tempfile.mkdtemp()

        for file_ in files:
            local_path = os.path.join(local_dir, os.path.basename(file_))
            self.logger.info("downloading {!r}".format(file_))

            resp = requests.get(file_)
            if resp.status_code == 200:
                with open(local_path, "w") as fp:
                    fp.write(resp.text)
        return local_dir

    def _build_gluubase(self):
        """Builds gluubase image.

        :param salt_master_ipaddr: IP address of salt-master.
        :returns: ``True`` if image successfully built, otherwise ``False``
        """
        build_succeed = True

        if not self.image_exists("gluubase"):
            # There must be a better way than to hard code every file one by one
            DOCKER_REPO = 'https://raw.githubusercontent.com/GluuFederation' \
                          '/gluu-docker/master/ubuntu/14.04'
            minion_file = DOCKER_REPO + '/gluubase/minion'
            supervisor_conf = DOCKER_REPO + '/gluubase/supervisord.conf'
            render = DOCKER_REPO + '/gluubase/render.sh'
            dockerfile = DOCKER_REPO + '/gluubase/Dockerfile'
            files = [minion_file, supervisor_conf, render, dockerfile]
            build_dir = self.get_remote_files(*files)
            build_succeed = self.build_image(build_dir, "gluubase")
            shutil.rmtree(build_dir)
        return build_succeed

    def setup_container(self, name, image, dockerfile,
                        salt_master_ipaddr, port_bindings=None):
        """Builds and runs a container.

        :param name: Container name.
        :param image: Image name.
        :param dockerfile: Path to remote Dockerfile. Used to build the image
                        if image is not exist.
        :returns: Container ID in long format if container running successfully,
                otherwise an empty string.
        """
        if not self._build_gluubase():
            return ""

        # a flag to determine whether build image process is succeed
        build_succeed = True

        if not self.image_exists(image):
            build_dir = self.get_remote_files(dockerfile)
            build_succeed = self.build_image(build_dir, image)
            shutil.rmtree(build_dir)

        if build_succeed:
            return self.run_container(name, image, port_bindings=port_bindings)
        return ""

    def get_container_ip(self, container_id):
        """Gets container IP.

        :param container_id: Container ID; ideally the short format.
        :returns: Container's IP address.
        """
        info = self.docker.inspect_container(container_id)
        return info["NetworkSettings"]["IPAddress"]

    def remove_container(self, container_id):
        """Removes container.
        """
        try:
            return self.docker.remove_container(container_id, force=True)
        except docker.errors.APIError as exc:
            err_code = exc.response.status_code
            if err_code == 404:
                self.logger.warn(
                    "container {!r} does not exist".format(container_id))

    def inspect_container(self, container_id):
        return self.docker.inspect_container(container_id)

    def start_container(self, container_id):
        return self.docker.start(container_id)
