# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from schematics.types import BooleanType
from schematics.types import IntType
from schematics.types import StringType
from schematics.types.compound import PolyModelType
from sqlalchemy import JSON
from sqlalchemy import Unicode


from .base import BaseModel
from ..database import db


class BaseProvider(BaseModel):
    def is_in_use(self):
        """Checks whether the provider has linked nodes.

        :returns: True if provider has any node, otherwise False.
        """
        condition = {"provider_id": self.id}
        return bool(db.count_from_table("nodes", condition))

    def _resolve_driver_attr(self, field):
        try:
            return self.driver_attrs.get(field)
        except (AttributeError, TypeError,):
            return self._initial.get(field)

    @property
    def column_types(self):
        return {
            "driver_attrs": JSON,
            "name": Unicode(255),
            "driver": Unicode(128),
        }


class GenericProvider(BaseProvider):
    """This class represents entity for generic provider.
    """

    class DriverAttrs(BaseModel):
        generic_ip_address = StringType()
        generic_ssh_key = StringType()
        generic_ssh_user = StringType()
        generic_ssh_port = IntType()

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    driver = StringType(default="generic")
    driver_attrs = PolyModelType(DriverAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'name': self.name,
            'driver': self.driver,
            "generic_ip_address": self.generic_ip_address,
            "generic_ssh_key": self.generic_ssh_key,
            "generic_ssh_user": self.generic_ssh_user,
            "generic_ssh_port": self.generic_ssh_port,
        }

    @property
    def generic_ip_address(self):
        return self._resolve_driver_attr("generic_ip_address")

    @property
    def generic_ssh_key(self):
        return self._resolve_driver_attr("generic_ssh_key")

    @property
    def generic_ssh_user(self):
        return self._resolve_driver_attr("generic_ssh_user")

    @property
    def generic_ssh_port(self):
        return self._resolve_driver_attr("generic_ssh_port")


class DigitalOceanProvider(BaseProvider):
    class DriverAttrs(BaseModel):
        digitalocean_access_token = StringType()
        digitalocean_backups = BooleanType(default=False)
        digitalocean_private_networking = BooleanType(default=False)
        digitalocean_region = StringType()
        digitalocean_size = StringType(default="4gb")
        digitalocean_image = StringType(default="ubuntu-14-04-x64")
        digitalocean_ipv6 = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    driver = StringType(default="digitalocean")
    driver_attrs = PolyModelType(DriverAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'name': self.name,
            'driver': self.driver,
            "digitalocean_backups": self.digitalocean_backups,
            "digitalocean_private_networking": self.digitalocean_private_networking,  # noqa
            "digitalocean_region": self.digitalocean_region,
            "digitalocean_size": self.digitalocean_size,
            "digitalocean_image": self.digitalocean_image,
        }

    @property
    def digitalocean_access_token(self):
        return self._resolve_driver_attr("digitalocean_access_token")

    @property
    def digitalocean_backups(self):
        return self._resolve_driver_attr("digitalocean_backups")

    @property
    def digitalocean_private_networking(self):
        return self._resolve_driver_attr("digitalocean_private_networking")

    @property
    def digitalocean_region(self):
        return self._resolve_driver_attr("digitalocean_region")

    @property
    def digitalocean_size(self):
        return self._resolve_driver_attr("digitalocean_size")

    @property
    def digitalocean_image(self):
        return self._resolve_driver_attr("digitalocean_image")

    @property
    def digitalocean_ipv6(self):
        return self._resolve_driver_attr("digitalocean_ipv6")


class AwsProvider(BaseProvider):
    class DriverAttrs(BaseModel):
        amazonec2_access_key = StringType()
        amazonec2_secret_key = StringType()
        amazonec2_ami = StringType(default="ami-5f709f34")
        amazonec2_instance_type = StringType(default="m4.large")
        amazonec2_region = StringType()
        amazonec2_private_address_only = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    driver = StringType(default="amazonec2")
    driver_attrs = PolyModelType(DriverAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'name': self.name,
            'driver': self.driver,
            "amazonec2_ami": self.amazonec2_ami,
            "amazonec2_instance_type": self.amazonec2_instance_type,
            "amazonec2_region": self.amazonec2_region,
            "amazonec2_private_address_only": self.amazonec2_private_address_only,  # noqa
        }

    @property
    def amazonec2_access_key(self):
        return self._resolve_driver_attr("amazonec2_access_key")

    @property
    def amazonec2_secret_key(self):
        return self._resolve_driver_attr("amazonec2_secret_key")

    @property
    def amazonec2_ami(self):
        return self._resolve_driver_attr("amazonec2_ami")

    @property
    def amazonec2_instance_type(self):
        return self._resolve_driver_attr("amazonec2_instance_type")

    @property
    def amazonec2_region(self):
        return self._resolve_driver_attr("amazonec2_region")

    @property
    def amazonec2_private_address_only(self):
        return self._resolve_driver_attr("amazonec2_private_address_only")


class RackspaceProvider(BaseProvider):
    pass
