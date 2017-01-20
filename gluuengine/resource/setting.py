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

        try:
            ldap_setting = db.all("ldap_settings")[0]
        except IndexError:
            ldap_setting = LdapSetting(data)
            db.persist(ldap_setting, "ldap_settings")
        else:
            for k, v in data.iteritems():
                setattr(ldap_setting, k, v)
            db.update(ldap_setting.id, ldap_setting, "ldap_settings")
        finally:
            return ldap_setting.as_dict()

    def get(self):
        try:
            ldap_setting = db.all("ldap_settings")[0]
        except IndexError:
            return {}
        else:
            return ldap_setting.as_dict()

    def delete(self):
        try:
            ldap_setting = db.all("ldap_settings")[0]
        except IndexError:
            ldap_setting = {}
        else:
            db.delete(ldap_setting.id, "ldap_settings")
        finally:
            return {}, 204
