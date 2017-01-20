# -*- coding: utf-8 -*-
# Copyright (c) 2017 Gluu
#
# All rights reserved.

import uuid

from schematics.types import IntType
from schematics.types import StringType

from .base import BaseModel


class LdapSetting(BaseModel):
    id = StringType(default=lambda: str(uuid.uuid4()))
    host = StringType()
    port = IntType()
    bind_dn = StringType()
    encoded_bind_password = StringType()
    encoded_salt = StringType()
    inum_appliance = StringType()
    inum_org = StringType()
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "bind_dn": self.bind_dn,
            "inum_appliance": self.inum_appliance,
            # "inum_org": self.inum_org,
        }
