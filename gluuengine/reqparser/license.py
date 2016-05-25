# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re
from urllib import quote_plus

from marshmallow import post_load

from ..extensions import ma

MIDDLE_SPACES_RE = re.compile(r'(.+)\s+([^\s])')


class LicenseKeyReq(ma.Schema):
    name = ma.Str(required=True)
    code = ma.Str(required=True)
    public_key = ma.Str(required=True)
    public_password = ma.Str(required=True)
    license_password = ma.Str(required=True)

    @post_load
    def urlsafe_public_key(self, data):
        """Transform public key value into URL-safe string

        :param data: A ``dict`` contains public key value.
        """
        # public key from license server is not URL-safe
        # client like ``curl`` will interpret ``+`` as whitespace
        # hence we're converting whitespace to ``+``
        if "public_key" in data:
            data["public_key"] = quote_plus(data["public_key"], safe="/+=")
        return data
