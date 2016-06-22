# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from .base import BaseModel
from .base import STATE_SUCCESS
from ..database import db
from ..utils import get_quad
from ..utils import get_random_chars
from ..utils import encrypt_text
from ..utils import decrypt_text
from ..utils import generate_passkey
from ..utils import ldap_encode


class Cluster(BaseModel):
    resource_fields = dict.fromkeys([
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
        "external_ldap",
        "external_ldap_host",
        "external_ldap_port",
        "external_ldap_binddn",
        "external_ldap_inum_appliance",
    ])

    def __init__(self, fields=None):
        fields = fields or {}

        # Cluster unique identifier
        self.id = "{}".format(uuid.uuid4())

        # Cluster name
        self.name = fields.get("name")

        # Description of cluster
        self.description = fields.get("description")

        self.ox_cluster_hostname = fields.get("ox_cluster_hostname")
        self.ldaps_port = "1636"
        self.ldap_binddn = "cn=directory manager"

        # Name of org for X.509 certificate
        self.org_name = fields.get("org_name")

        # Short name of org for X.509 certificate
        self.org_short_name = fields.get("org_short_name")

        # ISO 3166-1 alpha-2 country code
        self.country_code = fields.get("country_code")

        # City for X.509 certificate
        self.city = fields.get("city")

        # State or province for X.509 certificate
        self.state = fields.get("state")

        # Admin email address for X.509 certificate
        self.admin_email = fields.get("admin_email")

        # pass key
        self.passkey = generate_passkey()

        # Secret for ldap cn=directory manager, and oxTrust admin
        admin_pw = fields.get("admin_pw", get_random_chars())
        self.admin_pw = encrypt_text(admin_pw, self.passkey)
        self.encoded_ldap_pw = ldap_encode(admin_pw)
        self.encoded_ox_ldap_pw = self.admin_pw

        # Unique identifier for domain
        self.base_inum = '@!%s.%s.%s.%s' % tuple([get_quad() for i in xrange(4)])

        # Unique identifier for organization
        org_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inum_org = '%s!0001!%s' % (self.base_inum, org_quads)

        # Unique identifier for cluster
        appliance_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inum_appliance = '%s!0002!%s' % (self.base_inum, appliance_quads)

        # Unique organization identifier sans special characters
        self.inum_org_fn = self.inum_org.replace('@', '').replace('!', '').replace('.', '')

        # Unique cluster identifier sans special characters
        self.inum_appliance_fn = self.inum_appliance.replace('@', '').replace('!', '').replace('.', '')

        # ox-related attrs
        client_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.oxauth_client_id = '%s!0008!%s' % (self.inum_org, client_quads)
        oxauth_client_pw = get_random_chars()
        self.oxauth_client_encoded_pw = encrypt_text(oxauth_client_pw, self.passkey)

        # scim-related attrs
        scim_rs_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.scim_rs_client_id = '%s!0008!%s' % (self.inum_org, scim_rs_quads)
        scim_rp_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.scim_rp_client_id = '%s!0008!%s' % (self.inum_org, scim_rp_quads)

        # key store for oxIdp
        self.encoded_shib_jks_pw = self.admin_pw
        self.shib_jks_fn = "/etc/certs/shibIDP.jks"

        # key store for oxAsimba
        self.encoded_asimba_jks_pw = self.admin_pw
        self.asimba_jks_fn = "/etc/certs/asimbaIDP.jks"

        # a flag to decide whether `external_ldap_*` attributes
        # should be filled
        self.external_ldap = fields.get(
            "external_ldap",
            False,
        )
        self.external_ldap_host = fields.get(
            "external_ldap_host",
            "",
        )
        self.external_ldap_port = fields.get(
            "external_ldap_port",
            "",
        )
        self.external_ldap_binddn = fields.get(
            "external_ldap_binddn",
            "",
        )
        self.external_ldap_encoded_password = fields.get(
            "external_ldap_encoded_password",
            "",
        )
        self.external_ldap_inum_appliance = fields.get(
            "external_ldap_inum_appliance",
            "",
        )
        self.external_encoded_salt = fields.get(
            "external_encoded_salt",
            "",
        )

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
