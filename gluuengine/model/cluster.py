# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

# from schematics.types import BooleanType
# from schematics.types import IntType
from schematics.types import StringType

from ._schema import CLUSTER_SCHEMA
from .base import BaseModel
from .base import STATE_SUCCESS
from ..database import db
from ..utils import decrypt_text


class Cluster(BaseModel):
    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    description = StringType()
    ox_cluster_hostname = StringType()
    org_name = StringType()
    country_code = StringType()
    city = StringType()
    state = StringType()
    admin_email = StringType()
    passkey = StringType()
    admin_pw = StringType()
    # encoded_ldap_pw = StringType()
    # encoded_ox_ldap_pw = StringType()
    # base_inum = StringType()
    # inum_org = StringType()
    # inum_org_fn = StringType()
    # inum_appliance = StringType()
    # inum_appliance_fn = StringType()
    # oxauth_client_id = StringType()
    # oxauth_client_encoded_pw = StringType()
    # oxauth_openid_jks_pass = StringType()
    # scim_rs_client_id = StringType()
    # scim_rs_client_jks_pass = StringType()
    # scim_rs_client_jks_pass_encoded = StringType()
    # scim_rp_client_id = StringType()
    # scim_rp_client_jks_pass = StringType()
    # encoded_shib_jks_pw = StringType()
    # encoded_asimba_jks_pw = StringType()
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ox_cluster_hostname': self.ox_cluster_hostname,
            'org_name': self.org_name,
            'country_code': self.country_code,
            'city': self.city,
            'state': self.state,
            'admin_email': self.admin_email,
            # 'base_inum': self.base_inum,
            # 'inum_org': self.inum_org,
            # 'inum_appliance': self.inum_appliance,
        }

    @property
    def decrypted_admin_pw(self):
        """Gets decrypted admin password.
        """
        return decrypt_text(self.admin_pw, self.passkey)

    def count_containers(self, type_="", state=STATE_SUCCESS):
        """Counts available containers objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = {"cluster_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return db.count_from_table("containers", condition)

    def get_containers(self, type_="", state=STATE_SUCCESS):
        """Gets available container objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = {"cluster_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return db.search_from_table("containers", condition)

    @property
    def _schema(self):
        return CLUSTER_SCHEMA

    @property
    def shib_jks_fn(self):
        return "/etc/certs/shibIDP.jks"

    @property
    def scim_rp_client_jks_fn(self):
        return "/etc/certs/scim-rp.jks"

    @property
    def scim_rs_client_jks_fn(self):
        return "/etc/certs/scim-rs.jks"

    @property
    def oxauth_openid_jks_fn(self):
        return "/etc/certs/oxauth-keys.jks"

    @property
    def asimba_jks_fn(self):
        return "/etc/certs/asimbaIDP.jks"
