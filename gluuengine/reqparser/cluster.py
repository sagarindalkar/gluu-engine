# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from marshmallow import validates
from marshmallow import ValidationError
from marshmallow import post_load

from ..extensions import ma
from ..utils import generate_passkey
from ..utils import encrypt_text
from ..utils import ldap_encode
from ..utils import get_quad
from ..utils import get_random_chars

# cluster name rule:
#
# * at least 3 chars
# * must not start with dash, underscore, dot, or number
# * must not end with dash, underscore, or dot
CLUSTER_NAME_RE = re.compile(r"^[a-zA-Z0-9]+[a-zA-Z0-9-_\.]+[a-zA-Z0-9]$")


class ExternalLDAPMixin(object):
    external_ldap = ma.Bool(missing=False)
    external_ldap_host = ma.Str(missing="")
    external_ldap_port = ma.Int(missing=0)
    external_ldap_binddn = ma.Str(missing="")
    external_ldap_encoded_password = ma.Str(missing="")
    external_encoded_salt = ma.Str(missing="")
    external_ldap_inum_appliance = ma.Str(missing="")

    @validates("external_ldap_host")
    def validate_external_ldap_host(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")

    @validates("external_ldap_port")
    def validate_external_ldap_port(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")

    @validates("external_ldap_binddn")
    def validate_external_ldap_binddn(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")

    @validates("external_ldap_inum_appliance")
    def validate_external_ldap_inum_appliance(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")

    @validates("external_ldap_encoded_password")
    def validate_external_ldap_encoded_password(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")

    @validates("external_encoded_salt")
    def validate_external_encoded_salt(self, value):
        if self.context.get("external_ldap") and not value:
            raise ValidationError("Field is required when "
                                  "external_ldap is enabled")


class ClusterReq(ExternalLDAPMixin, ma.Schema):
    name = ma.Str(required=True)
    description = ma.Str(missing="")
    ox_cluster_hostname = ma.Str(required=True)
    org_name = ma.Str(required=True)
    org_short_name = ma.Str(required=True)
    country_code = ma.Str(required=True)
    city = ma.Str(required=True)
    state = ma.Str(required=True)
    admin_email = ma.Email(required=True)
    admin_pw = ma.Str(required=True)

    @validates("country_code")
    def validate_country_code(self, value):
        """Validates cluster's country code.

        :param value: Cluster's country code.
        """
        if len(value) != 2:
            raise ValidationError("requires 2 characters")

    @validates("admin_pw")
    def validate_admin_pw(self, value):
        """Validates cluster's admin password.

        :param value: Cluster's admin password.
        """
        if len(value) < 6:
            raise ValidationError("Must use at least 6 characters")

    @validates("name")
    def validate_name(self, value):
        """Validates cluster's name.

        :param value: Cluster's name.
        """
        if not CLUSTER_NAME_RE.match(value):
            raise ValidationError("Unaccepted cluster name format")

    @post_load
    def finalize_data(self, data):
        plain_admin_pw = data["admin_pw"]
        org_quads = '{}.{}'.format(*[get_quad() for _ in xrange(2)])
        appliance_quads = '{}.{}'.format(*[get_quad() for _ in xrange(2)])
        client_quads = '{}.{}'.format(*[get_quad() for _ in xrange(2)])
        oxauth_client_pw = get_random_chars()
        scim_rs_quads = '{}.{}'.format(*[get_quad() for _ in xrange(2)])
        scim_rp_quads = '{}.{}'.format(*[get_quad() for i in xrange(2)])

        data["ldaps_port"] = "1636"
        data["ldap_binddn"] = "cn=directory manager"

        data["passkey"] = generate_passkey()
        data["admin_pw"] = encrypt_text(plain_admin_pw, data["passkey"])
        data["encoded_ldap_pw"] = ldap_encode(plain_admin_pw)
        data["encoded_ox_ldap_pw"] = data["admin_pw"]

        data["base_inum"] = "@!{}.{}.{}.{}".format(
            *[get_quad() for _ in xrange(4)]
        )

        data["inum_org"] = '{}!0001!{}'.format(data["base_inum"], org_quads)

        data["inum_appliance"] = '{}!0002!{}'.format(
            data["base_inum"], appliance_quads,
        )

        data["inum_org_fn"] = (
            data["inum_org"].replace('@', '')
                            .replace('!', '')
                            .replace('.', '')
        )

        data["inum_appliance_fn"] = (
            data["inum_appliance"].replace('@', '')
                                  .replace('!', '')
                                  .replace('.', '')
        )

        data["oxauth_client_id"] = '{}!0008!{}'.format(
            data["inum_org"], client_quads,
        )

        data["oxauth_client_encoded_pw"] = encrypt_text(
            oxauth_client_pw, data["passkey"],
        )

        data["oxauth_openid_jks_fn"] = "/etc/certs/oxauth-keys.jks"
        data["oxauth_openid_jks_pass"] = get_random_chars()

        data["scim_rs_client_id"] = '{}!0008!{}'.format(
            data["inum_org"], scim_rs_quads,
        )

        data["scim_rs_client_jks_fn"] = "/etc/certs/scim-rs.jks"
        data["scim_rs_client_jks_pass"] = get_random_chars()

        data["scim_rs_client_jks_pass_encoded"] = encrypt_text(
            data["scim_rs_client_jks_pass"], data["passkey"],
        )

        data["scim_rp_client_id"] = '{}!0008!{}'.format(
            data["inum_org"], scim_rp_quads,
        )

        data["scim_rp_client_jks_fn"] = "/etc/certs/scim-rp.jks"
        data["scim_rp_client_jks_pass"] = "secret"

        data["encoded_shib_jks_pw"] = data["admin_pw"]
        data["shib_jks_fn"] = "/etc/certs/shibIDP.jks"

        data["encoded_asimba_jks_pw"] = data["admin_pw"]
        data["asimba_jks_fn"] = "/etc/certs/asimbaIDP.jks"
        return data


class ClusterUpdateReq(ExternalLDAPMixin, ma.Schema):
    pass
