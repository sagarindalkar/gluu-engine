# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid
import itertools

from netaddr import IPNetwork
from netaddr import IPSet

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

        # Weave IP network
        self.weave_ip_network = fields.get("weave_ip_network", "10.2.1.0/24")

    @property
    def decrypted_admin_pw(self):
        """Gets decrypted admin password.
        """
        return decrypt_text(self.admin_pw, self.passkey)

    def get_ldap_objects(self, state=STATE_SUCCESS):
        """Get available ldap objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of ldap objects.
        """
        return self.get_node_objects(type_="ldap", state=state)

    def get_oxauth_objects(self, state=STATE_SUCCESS):
        """Get available oxAuth objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of oxauth objects.
        """
        return self.get_node_objects(type_="oxauth", state=state)

    def get_oxtrust_objects(self, state=STATE_SUCCESS):
        """Get available oxTrust objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of oxtrust objects.
        """
        return self.get_node_objects(type_="oxtrust", state=state)

    def get_httpd_objects(self, state=STATE_SUCCESS):
        """Get available httpd objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of httpd objects.
        """
        return self.get_node_objects(type_="httpd", state=state)

    def get_oxidp_objects(self, state=STATE_SUCCESS):
        """Get available oxidp objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of oxidp objects.
        """
        return self.get_node_objects(type_="oxidp", state=state)

    def get_nginx_objects(self, state=STATE_SUCCESS):
        """Get available nginx objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :returns: A list of nginx objects.
        """
        return self.get_node_objects(type_="nginx", state=state)

    def get_oxasimba_objects(self, state=STATE_SUCCESS):
        """Get available oxasimba objects (models).
        """
        return self.get_node_objects(type_="oxasimba", state=state)

    def get_node_objects(self, type_="", state=STATE_SUCCESS):
        """Gets available node objects (models).

        :param state: State of the node (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the node.
        :returns: A list of node objects.
        """
        condition = db.where("cluster_id") == self.id
        if state:
            condition = (condition) & (db.where("state") == state)
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.search_from_table("nodes", condition)

    @property
    def exposed_weave_ip(self):
        """Gets weave IP for forwarding request from outside.

        For convenience, the IP address is always set to the last 2nd IP of
        possible addresses from the network. For example, given an IP network
        10.10.10.0/24, two last addresses would be:

        1. 10.10.10.255 (broadcast address; we cannot use it)
        2. 10.10.10.254 (used by weave network to forward request from outside)

        :returns: A 2-elements tuple consists of IP address and prefix length,
                  e.g. ``("10.10.10.253", 24)``.
        """

        pool = IPNetwork(self.weave_ip_network)
        # as the last element of pool is a broadcast address, we cannot use it;
        # hence we fetch the last 2nd element of the pool
        addr = pool.broadcast - 1
        return str(addr), pool.prefixlen

    def reserve_ip_addr(self):
        """Picks available IP address from weave network.

        :returns: A 2-elements tuple consists of IP address and CIDR,
                  e.g. ``("10.10.10.1", 24)``. If there's no available
                  IP address anymore, this returns ``(None, 24)``.
        """
        # represents a pool of IP addresses
        pool = IPNetwork(self.weave_ip_network)

        reserved_addrs = IPSet([
            pool.network,
            pool.broadcast,
            self.exposed_weave_ip[0],
            self.prometheus_weave_ip[0],
        ] + self.get_node_addrs())
        maybe_available = IPSet(pool)
        ipset = reserved_addrs ^ maybe_available

        try:
            addr = list(itertools.islice(ipset, 1))[0]
        except IndexError:
            addr = ""
        return str(addr), pool.prefixlen

    @property
    def nodes_count(self):
        """Gets total number of nodes belong to cluster.

        :returns: Total number of nodes.
        """
        condition = db.where("cluster_id") == self.id
        return db.count_from_table("nodes", condition)

    @property
    def prometheus_weave_ip(self):
        """Gets weave IP of prometheus container.

        For convenience, the IP address is always set to the last 3rd IP of
        possible addresses from the network. For example, given an IP network
        10.10.10.0/24, three last addresses would be:

        1. 10.10.10.255 (broadcast address; we cannot use it)
        2. 10.10.10.254 (used by weave network to forward request from outside)
        2. 10.10.10.253 (prometheus weave IP)

        :returns: A 2-elements tuple consists of IP address and prefix length,
                  e.g. ``("10.10.10.253", 24)``.
        """
        pool = IPNetwork(self.weave_ip_network)
        # as the last element of pool is a broadcast address, we cannot use it;
        # hence we fetch the last 3rd element of the pool
        addr = pool.broadcast - 2
        return str(addr), pool.prefixlen

    def get_node_addrs(self):
        """Collects all weave IP addresses from all nodes belong to the cluster.

        :returns: A list of weave IP addresses.
        """
        nodes = db.search_from_table(
            "nodes",
            db.where("cluster_id") == self.id,
        )
        return filter(None, [node.weave_ip for node in nodes])
