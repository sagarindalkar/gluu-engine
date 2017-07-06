# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import re

from marshmallow import post_load
from marshmallow import validates
from marshmallow import ValidationError
from marshmallow.validate import OneOf

from ..extensions import ma

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')
NAME_RE = re.compile('^[a-zA-Z0-9_]+$')
USERNAME_RE = re.compile('^[a-z_][a-z0-9_-]*[$]?$')
# DRIVERS = ['generic', 'amazonec2', 'digitalocean', 'google']


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

    @post_load
    def finalize_data(self, data):
        data["driver_attrs"] = {
            "generic_ip_address": data.pop("generic_ip_address"),
            "generic_ssh_key": data.pop("generic_ssh_key"),
            "generic_ssh_user": data.pop("generic_ssh_user"),
            "generic_ssh_port": data.pop("generic_ssh_port"),
        }
        return data


#: List of all DigitalOcean regions.
#: https://developers.digitalocean.com/documentation/v2/#list-all-regions
DO_REGION_CHOICES = (
    "nyc1",  # New York 1
    "nyc2",  # New York 2
    "nyc3",  # New York 3
    # "ams1",  # Amsterdam 1
    "ams2",  # Amsterdam 2
    "ams3",  # Amsterdam 3
    "sgp1",  # Singapore 1
    "lon1",  # London 1
    "sfo1",  # San Fransisco 1
    "tor1",  # Toronto 1
    "fra1",  # Frankfurt 1
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

    # Digital Ocean Image
    digitalocean_image = ma.Str(missing="ubuntu-14-04-x64")

    # enable ipv6 for droplet
    digitalocean_ipv6 = ma.Bool(missing=False)

    # enable private networking for droplet
    digitalocean_private_networking = ma.Bool(default=False)

    # Digital Ocean region
    digitalocean_region = ma.Str(
        required=True, validate=OneOf(DO_REGION_CHOICES),
    )

    # Digital Ocean size
    digitalocean_size = ma.Str(validate=OneOf(DO_SIZE_CHOICES), default="4gb")

    @post_load
    def finalize_data(self, data):
        data["driver_attrs"] = {
            "digitalocean_access_token": data.pop("digitalocean_access_token"),
            "digitalocean_backups": data.pop("digitalocean_backups"),
            "digitalocean_private_networking": data.pop("digitalocean_private_networking"),
            "digitalocean_region": data.pop("digitalocean_region"),
            "digitalocean_size": data.pop("digitalocean_size"),
            "digitalocean_image": data.pop("digitalocean_image"),
            "digitalocean_ipv6": data.pop("digitalocean_ipv6"),
        }
        return data


AWS_REGION_CHOICES = (
    'us-east-1',        # US East (N. Virginia)
    'us-west-2',        # US West (Oregon)
    'us-west-1',        # US West (N. California)
    'eu-west-1',        # EU (Ireland)
    'eu-central-1',     # EU (Frankfurt)
    'ap-southeast-1',   # Asia Pacific (Singapore)
    'ap-northeast-1',   # Asia Pacific (Tokyo)
    'ap-southeast-2',   # Asia Pacific (Sydney)
    'ap-northeast-2',   # Asia Pacific (Seoul)
    'sa-east-1',        # South America (São Paulo)
)

AWS_INSTANCE_TYPE_CHOICES = (
    't2.micro',
    'm4.large',     # 2    8
    'm4.xlarge',    # 4   16
    'm4.2xlarge',   # 8   32
    'm4.4xlarge',   # 16   64
    'm4.10xlarge',  # 40  160
)

#not implemented
#--amazonec2-vpc-id
#--amazonec2-zone
#--amazonec2-security-group

class AwsProviderReq(BaseProviderReq):
    amazonec2_access_key = ma.Str(required=True)
    amazonec2_secret_key = ma.Str(required=True)
    amazonec2_region = ma.Str(validate=OneOf(AWS_REGION_CHOICES))
    amazonec2_instance_type = ma.Str(validate=OneOf(AWS_INSTANCE_TYPE_CHOICES), default="m4.large")
    amazonec2_private_address_only = ma.Bool(default=False)
    amazonec2_ami = ma.Str(missing="ami-5f709f34")

    @post_load
    def finalize_data(self, data):
        data["driver_attrs"] = {
            "amazonec2_access_key": data.pop("amazonec2_access_key"),
            "amazonec2_secret_key": data.pop("amazonec2_secret_key"),
            "amazonec2_region": data.pop("amazonec2_region"),
            "amazonec2_instance_type": data.pop("amazonec2_instance_type"),
            "amazonec2_private_address_only": data.pop("amazonec2_private_address_only"),
            "amazonec2_ami": data.pop("amazonec2_ami"),
        }
        return data
