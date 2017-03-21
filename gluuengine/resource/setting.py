# -*- coding: utf-8 -*-
# Copyright (c) 2017 Gluu
#
# All rights reserved.

from flask import request
from flask_restful import Resource

from ..database import db
from ..model import LdapSetting
from ..reqparser import LdapSettingReq


class LdapSettingResource(Resource):
    def put(self):
        data, errors = LdapSettingReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }

        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        ldap_setting = LdapSetting.query.first()
        if not ldap_setting:
            ldap_setting = LdapSetting(**data)
        else:
            for k, v in data.iteritems():
                setattr(ldap_setting, k, v)

        db.session.add(ldap_setting)
        db.session.commit()
        return ldap_setting.as_dict()

    def get(self):
        ldap_setting = LdapSetting.query.first()
        if ldap_setting:
            return ldap_setting.as_dict()
        return {}

    def delete(self):
        ldap_setting = LdapSetting.query.first()
        if ldap_setting:
            db.session.delete(ldap_setting)
            db.session.commit()
        return {}, 204
