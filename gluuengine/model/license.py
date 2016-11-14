# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel
from ..database import db
from ..utils import decrypt_text
from ..utils import retrieve_current_date

from schematics.types import StringType
from schematics.types import BooleanType
from schematics.types import LongType
from schematics.types import IntType
from schematics.types import UUIDType
from schematics.types.compound import ListType
from schematics.types.compound import PolyModelType


class _LicenseMetadata(BaseModel):
    product = StringType()
    expiration_date = LongType()
    creation_date = LongType()
    active = BooleanType()
    license_count_limit = IntType()
    license_name = StringType()
    autoupdate = BooleanType()
    license_id = StringType()
    emails = ListType(StringType)
    customer_name = StringType()


class LicenseKey(BaseModel):
    resource_fields = (
        "id",
        "name",
        "code",
        "valid",
        "metadata",
        "updated_at",
    )

    id = UUIDType()
    name = StringType()
    code = StringType()
    public_key = StringType()
    public_password = StringType()
    license_password = StringType()
    signed_license = StringType()
    valid = BooleanType()
    updated_at = LongType()
    passkey = StringType()
    metadata = PolyModelType(_LicenseMetadata, strict=False)
    _pyobject = StringType()

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

    @property
    def is_active(self):
        return self.metadata.get("active") is True

    @property
    def auto_update(self):
        # for backward compatibility, license that doesn't have
        # autoupdate field is marked as having auto-update feature;
        # subsequent update will fetch the field and then we can apply
        # auto-update check
        if "autoupdate" not in self.metadata:
            return True
        return self.metadata.get("autoupdate") is True
