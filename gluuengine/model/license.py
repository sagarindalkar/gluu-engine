# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from sqlalchemy import JSON

from .node import Node
from ..extensions import db
from ..utils import decrypt_text
from ..utils import retrieve_current_date


class LicenseKey(db.Model):
    """This class represents entity for license key.
    """
    __tablename__ = "license_keys"

    # class Metadata(BaseModel):
    #     product = StringType()
    #     expiration_date = LongType()
    #     creation_date = LongType()
    #     active = BooleanType()
    #     license_count_limit = IntType()
    #     license_name = StringType()
    #     autoupdate = BooleanType()
    #     license_id = StringType()
    #     emails = ListType(StringType)
    #     customer_name = StringType()

    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    _metadata = db.Column("metadata", JSON)
    name = db.Column(db.Unicode(255))
    code = db.Column(db.Unicode(255))
    public_key = db.Column(db.Text)
    public_password = db.Column(db.Unicode(255))
    license_password = db.Column(db.Unicode(255))
    signed_license = db.Column(db.Text)
    valid = db.Column(db.Boolean)
    updated_at = db.Column(db.BigInteger)
    passkey = db.Column(db.Unicode(255))

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "valid": self.valid,
            "metadata": dict(self._metadata or {}),
            "updated_at": self.updated_at,
            "public_key": self.decrypted_public_key,
        }

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
        expiration_date = self._metadata.get("expiration_date")
        # expiration_date likely tampered
        if not expiration_date:
            return True
        current_date = retrieve_current_date()
        return current_date > expiration_date

    def get_workers(self):
        """Gets worker nodes.

        :returns: A list of worker node objects (if any).
        """
        return Node.query.filter_by(type="worker").all()

    def count_workers(self):
        """Counts worker nodes.

        :returns: Total number of worker node objects (if any).
        """
        return Node.query.filter_by(type="worker").count()

    @property
    def mismatched(self):
        return self._metadata.get("product") != "de"

    @property
    def is_active(self):
        return self._metadata.get("active") is True

    @property
    def auto_update(self):
        # for backward compatibility, license that doesn't have
        # autoupdate field is marked as having auto-update feature;
        # subsequent update will fetch the field and then we can apply
        # auto-update check
        if "autoupdate" not in self._metadata:
            return True
        return self._metadata.get("autoupdate") is True

    def as_dict(self):
        return self.resource_fields
