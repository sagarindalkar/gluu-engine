# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from sqlalchemy import JSON

from .base import BaseModelMixin
from ..extensions import db
from ..model import Node


class Provider(BaseModelMixin, db.Model):
    __tablename__ = "providers"

    name = db.Column(db.Unicode(255))
    driver = db.Column(db.Unicode(128))
    driver_attrs = db.Column(JSON)

    __mapper_args__ = {
        "polymorphic_on": driver,
        "polymorphic_identity": "provider",
    }

    def is_in_use(self):
        """Checks whether the provider has linked nodes.

        :returns: True if provider has any node, otherwise False.
        """
        return bool(Node.query.filter_by(provider_id=self.id).count())


class GenericProvider(Provider):
    """This class represents entity for generic provider.
    """
    __mapper_args__ = {
        "polymorphic_identity": "generic",
    }

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
        return self.driver_attrs["generic_ip_address"]

    @property
    def generic_ssh_key(self):
        return self.driver_attrs["generic_ssh_key"]

    @property
    def generic_ssh_user(self):
        return self.driver_attrs["generic_ssh_user"]

    @property
    def generic_ssh_port(self):
        return self.driver_attrs["generic_ssh_port"]


class DigitalOceanProvider(Provider):
    __mapper_args__ = {
        "polymorphic_identity": "digitalocean",
    }

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
            "digitalocean_ipv6": self.digitalocean_ipv6,
        }

    @property
    def digitalocean_access_token(self):
        return self.driver_attrs.get("digitalocean_access_token")

    @property
    def digitalocean_backups(self):
        return self.driver_attrs.get("digitalocean_backups")

    @property
    def digitalocean_private_networking(self):
        return self.driver_attrs.get("digitalocean_private_networking")

    @property
    def digitalocean_region(self):
        return self.driver_attrs.get("digitalocean_region")

    @property
    def digitalocean_size(self):
        return self.driver_attrs.get("digitalocean_size")

    @property
    def digitalocean_image(self):
        return self.driver_attrs.get("digitalocean_image")

    @property
    def digitalocean_ipv6(self):
        return self.driver_attrs.get("digitalocean_ipv6")


class AwsProvider(Provider):
    __mapper_args__ = {
        "polymorphic_identity": "aws",
    }

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
        return self.driver_attrs.get("amazonec2_access_key")

    @property
    def amazonec2_secret_key(self):
        return self.driver_attrs.get("amazonec2_secret_key")

    @property
    def amazonec2_ami(self):
        return self.driver_attrs.get("amazonec2_ami")

    @property
    def amazonec2_instance_type(self):
        return self.driver_attrs.get("amazonec2_instance_type")

    @property
    def amazonec2_region(self):
        return self.driver_attrs.get("amazonec2_region")

    @property
    def amazonec2_private_address_only(self):
        return self.driver_attrs.get("amazonec2_private_address_only")


# class RackspaceProvider(Provider):
#     pass
