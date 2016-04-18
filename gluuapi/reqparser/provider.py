# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import re

from marshmallow import validates
from marshmallow import ValidationError
from marshmallow.validate import OneOf
from docker.utils import parse_host
from docker.errors import DockerException

from ..extensions import ma
from ..database import db

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')
NAME_RE = re.compile('^[a-zA-Z0-9_]+$')
USERNAME_RE = re.compile('^[a-z_][a-z0-9_-]*[$]?$')

DRIVERS = ['generic','amazonec2','digitalocean', 'google']


def valid_ip(ip=''):
    if ip:
        return [0<=int(x)<256 for x in re.split('\.',re.match(r'^\d+\.\d+\.\d+\.\d+$',ip).group(0))].count(True)==4
    else:
        False


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
    generic_ssh_port = ma.Str(required=True)
 
    @validates("generic_ip_address")
    def validate_generic_ip_address(self, value):
        if not HOSTNAME_RE.match(value) and not valid_ip(value):
            raise ValidationError("invalid ip or hostname")
    
    #forcing user to put key first in path
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
        try:
            port = int(value)
        except ValueError:
            raise ValidationError("invalid number")

        if port != 22:
            if not (1024 <= port <= 49152):
                raise ValidationError("port must be 22 or 1024-49152")


class EditProviderReq(BaseProviderReq):
    @validates("hostname")
    def validate_hostname(self, value):
        """Validates provider's hostname.

        :param value: Provider's hostname.
        """
        provider = self.context.get("provider")

        # some provider like AWS uses dotted hostname,
        # e.g. ip-172-31-24-54.ec2.internal
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid:
            raise ValidationError("invalid hostname")

        if provider:
            # ensure hostname is unique (not taken by another provider)
            hostname_num = db.count_from_table(
                "providers",
                (db.where("hostname") == value) & (db.where("id") != provider.id),
            )
            if hostname_num:
                raise ValidationError("hostname has been taken by "
                                      "existing provider")
