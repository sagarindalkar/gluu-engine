# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from ..database import db
from .base import BaseModel
from ..utils import generate_passkey
from ..utils import encrypt_text
from ..utils import decrypt_text
from ..utils import retrieve_current_date


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
        """Gets decrypted admin password of the license.
        """
        return decrypt_text(self.public_key, self.passkey)

    @property
    def decrypted_public_password(self):
        """Gets decrypted public password of the license.
        """
        return decrypt_text(self.public_password, self.passkey)

    @property
    def decrypted_license_password(self):
        """Gets decrypted license password of the license.
        """
        return decrypt_text(self.license_password, self.passkey)

    @property
    def expired(self):
        """Gets expiration status.
        """
        expiration_date = self.metadata.get("expiration_date")
        # expiration_date likely tampered
        if not expiration_date:
            return True
        current_date = retrieve_current_date()
        return current_date > expiration_date

    def get_workers(self):
        """Gets worker nodes.

        :returns: A list of worker node objects (if any).
        """
        workers = db.search_from_table(
            "nodes", {"type": "worker"},
        )
        return workers

    def count_workers(self):
        """Counts worker nodes.

        :returns: Total number of worker node objects (if any).
        """
        counter = db.count_from_table(
            "nodes", {"type": "worker"},
        )
        return counter

    @property
    def mismatched(self):
        return self.metadata.get("product") != "de"
