# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from .base import BaseModel
from ..database import db


class BaseProvider(BaseModel):
    def is_in_use(self):
        """Checks whether the provider has linked nodes.

        :returns: True if provider has any node, otherwise False.
        """
        condition = {"provider_id": self.id}
        return bool(db.count_from_table("nodes", condition))


class GenericProvider(BaseProvider):
    resource_fields = dict.fromkeys([
        'id',
        'name',
        'driver',
        'generic_ip_address',
        'generic_ssh_key',
        'generic_ssh_user',
        'generic_ssh_port'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.driver = 'generic'
        self.populate(fields)

    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        self.generic_ip_address = fields.get('generic_ip_address', '')
        self.generic_ssh_key = fields.get('generic_ssh_key', '')
        self.generic_ssh_user = fields.get('generic_ssh_user', '')
        self.generic_ssh_port = fields.get('generic_ssh_port', '')


class DigitalOceanProvider(BaseProvider):
    resource_fields = dict.fromkeys([
        "id",
        "name",
        "driver",
        # "digitalocean_access_token",
        "digitalocean_backups",
        "digitalocean_private_networking",
        "digitalocean_region",
        "digitalocean_size",
        "digitalocean_image",
        "digitalocean_ipv6",
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.driver = "digitalocean"
        self.digitalocean_image = "ubuntu-14-04-x64"
        self.digitalocean_ipv6 = False
        self.populate(fields)

    def populate(self, fields=None):
        fields = fields or {}

        self.name = fields.get("name", "")
        self.digitalocean_access_token = fields.get(
            "digitalocean_access_token",
            "",
        )
        self.digitalocean_backups = fields.get(
            "digitalocean_backups",
            False,
        )
        # self.digitalocean_image = fields.get(
        #     "digitalocean_image",
        #     "ubuntu-14-04-x64",
        # )
        # self.digitalocean_ipv6 = fields.get(
        #     "digitalocean_ipv6",
        #     False,
        # )
        self.digitalocean_private_networking = fields.get(
            "digitalocean_private_networking",
            False,
        )
        self.digitalocean_region = fields.get(
            "digitalocean_region",
            "",
        )
        self.digitalocean_size = fields.get(
            "digitalocean_size",
            "4gb",
        )


class AwsProvider(BaseProvider):
    resource_fields = dict.fromkeys([
        'id',
        'name',
        'driver',
        # 'amazonec2_access_key',
        # 'amazonec2_secret_key',
        'amazonec2_ami',
        'amazonec2_instance_type',
        'amazonec2_region',
        'amazonec2_private_address_only',
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.driver = "amazonec2"
        self.amazonec2_ami = "ami-5f709f34"
        self.populate(fields)

    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        self.amazonec2_access_key = fields.get('amazonec2_access_key', '')
        self.amazonec2_secret_key = fields.get('amazonec2_secret_key', '')
        self.amazonec2_region = fields.get('amazonec2_region', '')
        self.amazonec2_instance_type = fields.get('amazonec2_instance_type', 'm4.large')
        self.amazonec2_private_address_only = fields.get('amazonec2_private_address_only', False)


class RackspaceProvider(BaseProvider):
    pass
