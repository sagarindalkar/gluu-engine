# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from marshmallow import validates
from marshmallow import ValidationError

from ..extensions import ma

# cluster name
#
# * at least 3 chars
# * must not start with dash, underscore, dot, or number
# * must not end with dash, underscore, or dot
CLUSTER_NAME_RE = re.compile(r"^[a-zA-Z0-9]+[a-zA-Z0-9-_\.]+[a-zA-Z0-9]$")


class ClusterReq(ma.Schema):
    name = ma.Str(required=True)
    description = ma.Str()
    ox_cluster_hostname = ma.Str(required=True)
    org_name = ma.Str(required=True)
    org_short_name = ma.Str(required=True)
    country_code = ma.Str(required=True)
    city = ma.Str(required=True)
    state = ma.Str(required=True)
    admin_email = ma.Email(required=True)
    admin_pw = ma.Str(required=True)

    @validates("country_code")
    def validate_country_code(self, value):
        """Validates cluster's country code.

        :param value: Cluster's country code.
        """
        if len(value) != 2:
            raise ValidationError("requires 2 characters")

    @validates("admin_pw")
    def validate_admin_pw(self, value):
        """Validates cluster's admin password.

        :param value: Cluster's admin password.
        """
        if len(value) < 6:
            raise ValidationError("Must use at least 6 characters")

    @validates("name")
    def validate_name(self, value):
        """Validates cluster's name.

        :param value: Cluster's name.
        """
        if not CLUSTER_NAME_RE.match(value):
            raise ValidationError("Unaccepted cluster name format")
