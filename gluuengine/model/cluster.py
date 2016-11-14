# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel
from .base import STATE_SUCCESS
from ..database import db
from ..utils import decrypt_text

from schematics.types import BooleanType
from schematics.types import IntType
from schematics.types import StringType
from schematics.types import UUIDType


class Cluster(BaseModel):
    resource_fields = (
        'id',
        'name',
        'description',
        'ox_cluster_hostname',
        'org_name',
        'org_short_name',
        'country_code',
        'city',
        'state',
        'admin_email',
        'base_inum',
        'inum_org',
        'inum_org_fn',
        'inum_appliance',
        'inum_appliance_fn',
        # "external_ldap",
        # "external_ldap_host",
        # "external_ldap_port",
        # "external_ldap_binddn",
        # "external_ldap_inum_appliance",
    )

    id = UUIDType()
    name = StringType()
    description = StringType()
    ox_cluster_hostname = StringType()
    ldaps_port = StringType()
    ldap_binddn = StringType()
    org_name = StringType()
    org_short_name = StringType()
    country_code = StringType()
    city = StringType()
    state = StringType()
    admin_email = StringType()
    passkey = StringType()
    admin_pw = StringType()
    encoded_ldap_pw = StringType()
    encoded_ox_ldap_pw = StringType()
    base_inum = StringType()
    inum_org = StringType()
    inum_org_fn = StringType()
    inum_appliance = StringType()
    inum_appliance_fn = StringType()
    oxauth_client_id = StringType()
    oxauth_client_encoded_pw = StringType()
    oxauth_openid_jks_fn = StringType()
    oxauth_openid_jks_pass = StringType()
    scim_rs_client_id = StringType()
    scim_rs_client_jks_fn = StringType()
    scim_rs_client_jks_pass = StringType()
    scim_rs_client_jks_pass_encoded = StringType()
    scim_rp_client_id = StringType()
    scim_rp_client_jks_fn = StringType()
    scim_rp_client_jks_pass = StringType()
    encoded_shib_jks_pw = StringType()
    shib_jks_fn = StringType()
    encoded_asimba_jks_pw = StringType()
    asimba_jks_fn = StringType()
    external_ldap = BooleanType()
    external_ldap_host = StringType()
    external_ldap_port = IntType()
    external_ldap_binddn = StringType()
    external_ldap_encoded_password = StringType()
    external_ldap_inum_appliance = StringType()
    external_encoded_salt = StringType()
    _pyobject = StringType()

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
