# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from netaddr import IPNetwork
from netaddr import IPAddress

from ..database import db
from .base import BaseModel
from .base import STATE_SUCCESS
from ..utils import get_quad
from ..utils import get_random_chars
from ..utils import encrypt_text
from ..utils import decrypt_text
from ..utils import generate_passkey
from ..utils import ldap_encode


class GluuCluster(BaseModel):
    resource_fields = dict.fromkeys([
        'id',
        'name',
        'description',
        'ox_cluster_hostname',
        'ldaps_port',
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
        'weave_ip_network',
    ])

    def __init__(self, fields=None):
        fields = fields or {}

        # GluuCluster unique identifier
        self.id = "{}".format(uuid.uuid4())

        # GluuCluster name
        self.name = fields.get("name")

        # Description of cluster
        self.description = fields.get("description")

        self.ldap_nodes = []
        self.oxauth_nodes = []
        self.oxtrust_nodes = []
        self.httpd_nodes = []
        self.ox_cluster_hostname = fields.get("ox_cluster_hostname")
        self.ldaps_port = "1636"

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
        self.oxauth_client_id = '%s!0008!%s' % (self.base_inum, client_quads)
        oxauth_client_pw = get_random_chars()
        self.oxauth_client_encoded_pw = encrypt_text(oxauth_client_pw, self.passkey)

        # key store
        self.encoded_shib_jks_pw = self.admin_pw
        self.shib_jks_fn = "/etc/certs/shibIDP.jks"

        # Weave IP network
        self.weave_ip_network = fields.get("weave_ip_network", "10.2.1.0/24")

        # a pointer to last fetched address
        self.last_fetched_addr = ""

    @property
    def decrypted_admin_pw(self):
        return decrypt_text(self.admin_pw, self.passkey)

    def get_ldap_objects(self, state=STATE_SUCCESS):
        """Get available ldap objects (models).
        """
        return self.get_node_objects(type_="ldap", state=state)

    def get_oxauth_objects(self, state=STATE_SUCCESS):
        """Get available oxAuth objects (models).
        """
        return self.get_node_objects(type_="oxauth", state=state)

    def get_oxtrust_objects(self, state=STATE_SUCCESS):
        """Get available oxTrust objects (models).
        """
        return self.get_node_objects(type_="oxtrust", state=state)

    def get_httpd_objects(self, state=STATE_SUCCESS):
        """Get available httpd objects (models).
        """
        return self.get_node_objects(type_="httpd", state=state)

    def get_oxidp_objects(self, state=STATE_SUCCESS):
        """Get available oxidp objects (models).
        """
        return self.get_node_objects(type_="oxidp", state=state)

    def get_node_objects(self, type_="", state=STATE_SUCCESS):
        condition = db.where("cluster_id") == self.id
        if state:
            if state == STATE_SUCCESS:
                # backward-compat for node without state field
                condition = (condition) & ((db.where("state") == STATE_SUCCESS) | (~db.where("state")))
            else:
                condition = (condition) & (db.where("state") == state)
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.search_from_table("nodes", condition)

    @property
    def exposed_weave_ip(self):
        pool = IPNetwork(self.weave_ip_network)
        # as the last element of pool is a broadcast address, we cannot use it;
        # hence we fetch the last 2nd element of the pool
        addr = pool[-2]
        return str(addr), pool.prefixlen

    def reserve_ip_addr(self):
        """Picks available IP address from weave network.

        :returns: A 2-elements tuple consists of IP address and CIDR,
                  e.g. ``("10.10.10.1", 24)``. If there's no available
                  IP address anymore, this returns ``(None, 24)``.
        """
        # represents a pool of IP addresses
        pool = IPNetwork(self.weave_ip_network)

        if self.last_fetched_addr:
            addr = str(IPAddress(self.last_fetched_addr) + 1)
        else:
            # skips ``pool.network`` address
            addr = str(pool[1])

        if addr in (self.exposed_weave_ip[0], str(pool.network),
                    str(pool.broadcast), self.prometheus_weave_ip[0]):
            # there's no available IP address
            return "", pool.prefixlen
        return addr, pool.prefixlen

    @property
    def prefixlen(self):
        return IPNetwork(self.weave_ip_network).prefixlen

    @property
    def nodes_count(self):
        condition = db.where("cluster_id") == self.id
        return db.count_from_table("nodes", condition)

    @property
    def prometheus_weave_ip(self):
        pool = IPNetwork(self.weave_ip_network)
        # as the last element of pool is a broadcast address, we cannot use it;
        # hence we fetch the last 3rd element of the pool
        addr = pool[-3]
        return str(addr), pool.prefixlen
