# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from ..database import db
from .base import BaseModel
from ..utils import generate_passkey
from ..utils import timestamp_millis
from ..utils import encrypt_text
from ..utils import decrypt_text


class LicenseKey(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "name",
        "code",
        "valid",
        "metadata",
    ])

    def __init__(self, fields=None):
        self.id = "{}".format(uuid.uuid4())
        self.passkey = generate_passkey()
        self.valid = False
        self.metadata = {}
        self.signed_license = ""
        self.populate(fields)

    def populate(self, fields=None):
        fields = fields or {}

        self.name = fields.get("name", "")
        self.code = fields.get("code", "")

        self.public_key = encrypt_text(
            fields.get("public_key", ""),
            self.passkey,
        )

        self.public_password = encrypt_text(
            fields.get("public_password", ""),
            self.passkey,
        )

        self.license_password = encrypt_text(
            fields.get("license_password", ""),
            self.passkey,
        )

    @property
    def decrypted_public_key(self):
        return decrypt_text(self.public_key, self.passkey)

    @property
    def decrypted_public_password(self):
        return decrypt_text(self.public_password, self.passkey)

    @property
    def decrypted_license_password(self):
        return decrypt_text(self.license_password, self.passkey)

    @property
    def expired(self):
        if not self.valid or not self.metadata:
            return True

        # ``expiration_date`` is set to null
        if not self.metadata["expiration_date"]:
            return False

        # ``expiration_date`` is time in milliseconds since the EPOCH
        now = timestamp_millis()
        return now > self.metadata["expiration_date"]

    def get_provider_objects(self):
        providers = db.search_from_table(
            "providers", db.where("type") == "consumer",
        )
        return providers
