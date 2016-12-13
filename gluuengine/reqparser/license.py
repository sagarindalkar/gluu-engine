# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re
from urllib import quote_plus

from marshmallow import post_load

from ..extensions import ma
from ..utils import generate_passkey
from ..utils import encrypt_text

MIDDLE_SPACES_RE = re.compile(r'(.+)\s+([^\s])')


class LicenseKeyReq(ma.Schema):
    name = ma.Str(required=True)
    code = ma.Str(required=True)
    public_key = ma.Str(required=True)
    public_password = ma.Str(required=True)
    license_password = ma.Str(required=True)

    @post_load
    def finalize_data(self, data):
        data["passkey"] = generate_passkey()

        # public key from license server is not URL-safe
        # client like ``curl`` will interpret ``+`` as whitespace
        # hence we're converting whitespace to ``+``;
        # we also encrypt the public_key
        data["public_key"] = encrypt_text(
            quote_plus(data["public_key"], safe="/+="),
            data["passkey"],
        )

        data["public_password"] = encrypt_text(
            data["public_password"], data["passkey"],
        )

        data["license_password"] = encrypt_text(
            data["license_password"], data["passkey"],
        )
        data["metadata"] = {}
        return data
