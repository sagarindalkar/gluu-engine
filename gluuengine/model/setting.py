# -*- coding: utf-8 -*-
# Copyright (c) 2017 Gluu
#
# All rights reserved.

from .base import BaseModelMixin
from ..extensions import db


class LdapSetting(BaseModelMixin, db.Model):
    __tablename__ = "ldap_settings"

    host = db.Column(db.Unicode(255))
    port = db.Column(db.Integer, default=1636)
    bind_dn = db.Column(db.Unicode(255))
    encoded_bind_password = db.Column(db.Unicode(255))
    encoded_salt = db.Column(db.Unicode(255))
    inum_appliance = db.Column(db.Unicode(255))
    inum_org = db.Column(db.Unicode(255))

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

    @property
    def inum_org_fn(self):
        return (
            self.inum_org.replace('@', '')
                         .replace('!', '')
                         .replace('.', '')
        )

    @property
    def inum_appliance_fn(self):
        return (
            self.inum_appliance.replace('@', '')
                               .replace('!', '')
                               .replace('.', '')
        )
