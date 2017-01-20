# -*- coding: utf-8 -*-
# Copyright (c) 2017 Gluu
#
# All rights reserved.

from ..extensions import ma


class LdapSettingReq(ma.Schema):
    host = ma.Str(required=True)
    port = ma.Int(missing=1636)
    bind_dn = ma.Str(missing="cn=directory manager,o=gluu")
    encoded_bind_password = ma.Str(required=True)
    encoded_salt = ma.Str(required=True)
    inum_appliance = ma.Str(required=True)
    inum_org = ma.Str(missing="")
