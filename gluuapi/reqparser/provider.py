# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import re

from marshmallow import validates
from marshmallow import ValidationError
from marshmallow.validate import OneOf

from ..extensions import ma

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')
NAME_RE = re.compile('^[a-zA-Z0-9_]+$')
USERNAME_RE = re.compile('^[a-z_][a-z0-9_-]*[$]?$')
DRIVERS = ['generic', 'amazonec2', 'digitalocean', 'google']


def valid_ip(ip):
    ip_matched = re.match(r'^\d+\.\d+\.\d+\.\d+$', ip)
    if not ip_matched:
        return False
    return [0 <= int(x) < 256 for x in re.split('\.', ip_matched.group(0))].count(True) == 4


class BaseProviderReq(ma.Schema):
    name = ma.Str(required=True)

    @validates("name")
    def validate_name(self, value):
        """Validates provider's name.

        :param value: Provider's name.
        """
        # no need to check for uniqueness
        valid = NAME_RE.match(value)
        if not valid:
            raise ValidationError("invalid name")


class GenericProviderReq(BaseProviderReq):
    generic_ip_address = ma.Str(required=True)
    generic_ssh_key = ma.Str(required=True)
    generic_ssh_user = ma.Str(required=True)
    generic_ssh_port = ma.Int(required=True)

    @validates("generic_ip_address")
    def validate_generic_ip_address(self, value):
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid and not valid_ip(value):
            raise ValidationError("invalid ip or hostname")

    # forcing user to put key first in path
    @validates("generic_ssh_key")
    def validate_generic_ssh_key(self, value):
        if not os.path.isfile(value):
            raise ValidationError("ssh key not found")

    @validates("generic_ssh_user")
    def validate_generic_ssh_user(self, value):
        if not (1 <= len(value) <= 31):
            raise ValidationError("username too long")
        elif not USERNAME_RE.match(value):
            raise ValidationError("invalid username")

    @validates("generic_ssh_port")
    def validate_generic_ssh_port(self, value):
        if value != 22:
            if not (1024 <= value <= 49152):
                raise ValidationError("port must be 22 or 1024 - 49152 range")


#: List of all DigitalOcean regions.
#: https://developers.digitalocean.com/documentation/v2/#list-all-regions
DO_REGION_CHOICES = (
    "nyc1",  # New York 1
    "nyc2",  # New York 2
    "nyc3",  # New York 3
    "ams1",  # Amsterdam 1
    "ams2",  # Amsterdam 2
    "ams3",  # Amsterdam 3
    "sgp1",  # Singapore 1
    "lon1",  # London 1
    "sfo1",  # San Fransisco 1
    "tor1",  # Toronto 1
)

#: List of all DigitalOcean sizes.
#: See https://developers.digitalocean.com/documentation/v2/#list-all-sizes
DO_SIZE_CHOICES = (
    "512mb",
    "1gb",
    "2gb",
    "4gb",
    "8gb",
    "16gb",
    "32gb",
    "48gb",
    "64gb",
)


class DigitalOceanProviderReq(BaseProviderReq):
    # Digital Ocean access token
    digitalocean_access_token = ma.Str(required=True)

    # enable backups for droplet
    digitalocean_backups = ma.Bool(default=False)

    # # Digital Ocean Image
    # digitalocean_image = ma.Str(default="ubuntu-14-04-x64")

    # # enable ipv6 for droplet
    # digitalocean_ipv6 = ma.Bool(default=False)

    # enable private networking for droplet
    digitalocean_private_networking = ma.Bool(default=False)

    # Digital Ocean region
    digitalocean_region = ma.Str(
        required=True, validate=OneOf(DO_REGION_CHOICES),
    )

    # Digital Ocean size
    digitalocean_size = ma.Str(validate=OneOf(DO_SIZE_CHOICES), default="4gb")
