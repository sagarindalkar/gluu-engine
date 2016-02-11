# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from ..database import db
from .base import BaseModel
from .base import STATE_SUCCESS


class Provider(BaseModel):
    """Provider is a model represents a Docker host.

    Docker host could be any reachable machine, either local or remote.
    """
    resource_fields = dict.fromkeys([
        "id",
        "docker_base_url",
        "hostname",
        "cluster_id",
        "type",
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.cluster_id = ""
        self.populate(fields)

    @property
    def nodes_count(self):
        """Gets total number of nodes belong to provider.

        :returns: Total number of nodes.
        """
        condition = db.where("provider_id") == self.id
        return db.count_from_table("nodes", condition)

    def get_node_objects(self, type_="", state=STATE_SUCCESS):
        """Gets available node objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the node.
        :returns: A list of node objects.
        """
        condition = db.where("provider_id") == self.id
        if type_:
            condition = (condition) & (db.where("type") == type_)
        if state:
            condition = (condition) & (db.where("state") == state)
        return db.search_from_table("nodes", condition)

    def populate(self, fields=None):
        fields = fields or {}

        self.docker_base_url = fields.get("docker_base_url", "")
        self.hostname = fields.get("hostname", "")
        self.type = fields.get("type", "")

        # Path to directory to store all docker client certs
        self.docker_cert_dir = fields.get("docker_cert_dir",
                                          "/etc/gluu/docker_certs")

    @property
    def ssl_cert_path(self):
        """Absolute path to SSL certificate used for making request
        to docker Remote API.
        """
        return "{}/{}__cert.pem".format(self.docker_cert_dir, self.id)

    @property
    def ssl_key_path(self):
        """Absolute path to SSL private key used for making request
        to docker Remote API.
        """
        return "{}/{}__key.pem".format(self.docker_cert_dir, self.id)

    @property
    def ca_cert_path(self):
        """Absolute path to CA certificate used for making request
        to docker Remote API.
        """
        return "{}/{}__ca.pem".format(self.docker_cert_dir, self.id)
