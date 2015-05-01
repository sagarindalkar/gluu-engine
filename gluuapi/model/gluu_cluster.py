# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import itertools
import uuid

from flask_restful_swagger import swagger
from flask_restful import fields as rest_fields
from netaddr import IPNetwork
from netaddr import IPSet

from gluuapi.database import db
from gluuapi.model.base import BaseModel
from gluuapi.helper import get_quad
from gluuapi.helper import get_random_chars
from gluuapi.helper import encrypt_text
from gluuapi.helper import decrypt_text
from gluuapi.helper import generate_passkey
from gluuapi.helper import ldap_encode


@swagger.model
class GluuCluster(BaseModel):
    # Swager Doc
    resource_fields = {
        'id': rest_fields.String(attribute='GluuCluster unique identifier'),
        'name': rest_fields.String(attribute='GluuCluster name'),
        'description': rest_fields.String(attribute='Description of cluster'),
        'ldap_nodes': rest_fields.List(rest_fields.String, attribute='Ids of ldap nodes'),  # noqa
        'oxauth_nodes': rest_fields.List(rest_fields.String, attribute='Ids of oxauth nodes'),  # noqa
        'oxtrust_nodes': rest_fields.List(rest_fields.String, attribute='Ids of oxtrust nodes'),  # noqa
        'hostname_ldap_cluster': rest_fields.String,
        'hostname_oxauth_cluster': rest_fields.String,
        'hostname_oxtrust_cluster': rest_fields.String,
        'ldaps_port': rest_fields.String,
        'orgName': rest_fields.String(attribute='Name of org for X.509 certificate'),  # noqa
        'orgShortName': rest_fields.String(attribute='Short name of org for X.509 certificate'),  # noqa
        'countryCode': rest_fields.String(attribute='ISO 3166-1 alpha-2 country code'),  # noqa
        'city': rest_fields.String(attribute='City for X.509 certificate'),
        'state': rest_fields.String(attribute='State or province for X.509 certificate'),  # noqa
        'admin_email': rest_fields.String(attribute='Admin email address for X.509 certificate'),  # noqa
        'baseInum': rest_fields.String(attribute='Unique identifier for domain'),
        'inumOrg': rest_fields.String(attribute='Unique identifier for organization'),  # noqa
        'inumOrgFN': rest_fields.String(attribute='Unique organization identifier sans special characters.'),  # noqa
        'inumAppliance': rest_fields.String(attribute='Unique identifier for cluster'),  # noqa
        'inumApplianceFN': rest_fields.String(attribute='Unique cluster identifier sans special characters.'),  # noqa
        'weave_ip_network': rest_fields.String(attribute='Weave IP network'),  # noqa
    }

    def __init__(self, fields=None):
        fields = fields or {}

        # GluuCluster unique identifier
        self.id = "{}".format(uuid.uuid4())
        self.name = fields.get("name")
        self.description = fields.get("description")
        self.ldap_nodes = []
        self.oxauth_nodes = []
        self.oxtrust_nodes = []
        self.hostname_ldap_cluster = fields.get("hostname_ldap_cluster")
        self.hostname_oxauth_cluster = fields.get("hostname_oxauth_cluster")
        self.hostname_oxtrust_cluster = fields.get("hostname_oxtrust_cluster")
        self.ldaps_port = "1636"

        # X.509 Certificate Information
        self.orgName = fields.get("orgName")
        self.orgShortName = fields.get("orgShortName")
        self.countryCode = fields.get("countryCode")
        self.city = fields.get("city")
        self.state = fields.get("state")
        self.admin_email = fields.get("admin_email")

        # pass key
        self.passkey = generate_passkey()

        # Secret for ldap cn=directory manager, and oxTrust admin
        admin_pw = fields.get("admin_pw", get_random_chars())
        self.admin_pw = encrypt_text(admin_pw, self.passkey)
        self.encoded_ldap_pw = ldap_encode(admin_pw)
        self.encoded_ox_ldap_pw = self.admin_pw

        # Inums
        self.baseInum = '@!%s.%s.%s.%s' % tuple([get_quad() for i in xrange(4)])

        org_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inumOrg = '%s!0001!%s' % (self.baseInum, org_quads)

        appliance_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inumAppliance = '%s!0002!%s' % (self.baseInum, appliance_quads)

        self.inumOrgFN = self.inumOrg.replace('@', '').replace('!', '').replace('.', '')
        self.inumApplianceFN = self.inumAppliance.replace('@', '').replace('!', '').replace('.', '')

        # ox-related attrs
        client_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.oxauth_client_id = '%s!0008!%s' % (self.baseInum, client_quads)
        oxauth_client_pw = get_random_chars()
        self.oxauth_client_encoded_pw = encrypt_text(oxauth_client_pw, self.passkey)

        # key store
        self.encoded_shib_jks_pw = self.admin_pw
        self.shib_jks_fn = "/etc/certs/shibIDP.jks"
        self.weave_ip_network = fields.get("weave_ip_network", "")
        self.reserved_ip_addrs = []

    def add_node(self, node):
        """Adds node into current cluster.

        ``Node.type`` determines where to put the node to.
        For example, node with ``ldap`` type will be appended to
        ``GluuCluster.ldap_nodes``.

        List of supported node types:

        * ``ldap``
        * ``oxauth``
        * ``oxtrust``

        :param node: an instance of any supported Node class.
        """
        node_type = getattr(node, "type")
        node_attr = self.node_type_map.get(node_type)
        if node_attr is None:
            raise ValueError("{!r} node is not supported".format(node_type))
        node_attr.append(node.id)

    def remove_node(self, node):
        """Removes node from current cluster.

        ``Node.type`` determines where to remove the node from.
        For example, node with ``ldap`` type will be removed from
        ``GluuCluster.ldap_nodes``.

        List of supported node types:

        * ``ldap``
        * ``oxauth``
        * ``oxtrust``

        :param node: an instance of any supported Node class.
        """
        node_type = getattr(node, "type")
        node_attr = self.node_type_map.get(node_type)
        if node_attr is None:
            raise ValueError("{!r} node is not supported".format(node_type))
        node_attr.remove(node.id)

    @property
    def node_type_map(self):
        node_type_map = {
            "ldap": self.ldap_nodes,
            "oxauth": self.oxauth_nodes,
            "oxtrust": self.oxtrust_nodes,
        }
        return node_type_map

    @property
    def decrypted_admin_pw(self):
        return decrypt_text(self.admin_pw, self.passkey)

    @property
    def max_allowed_ldap_nodes(self):
        return 4

    def get_ldap_hosts(self):
        ldap_hosts = []
        for ldap_id in self.ldap_nodes:
            ldap = db.get(ldap_id, "nodes")
            if ldap:
                ldap_host = "{}:{}".format(ldap.local_hostname,
                                           ldap.ldaps_port)
                ldap_hosts.append(ldap_host)
        return ldap_hosts

    def get_oxauth_objects(self):
        """Get available oxAuth objects (models).
        """
        return filter(
            None,
            [db.get(id_, "nodes") for id_ in self.oxauth_nodes],
        )

    def get_oxtrust_objects(self):
        """Get available oxTrust objects (models).
        """
        return filter(
            None,
            [db.get(id_, "nodes") for id_ in self.oxtrust_nodes],
        )

    def reserve_ip_addr(self):
        """Picks first available IP address from weave network.

        If there's no available IP address anymore, ``IndexError``
        will be raised. To prevent this error, catch the exception
        or checks the value ``GluuCluster.ip_addr_available`` first
        before trying to call this method.

        :returns: A 2-elements tuple consists of IP address and network prefix,
                  e.g. ``("10.10.10.1", 24)``.
        """
        # represents a pool of IP addresses
        pool = IPNetwork(self.weave_ip_network)

        # a generator holds possible IP addresses range
        ip_range = IPSet(pool.iter_hosts()) ^ IPSet(self.reserved_ip_addrs)

        # retrieves first IP address from ``ip_range`` generator
        ip_addr = list(itertools.islice(ip_range, 1))[0]

        # register the IP address so it will be excluded
        # from possible IP range in subsequent requests
        self.reserved_ip_addrs.append(str(ip_addr))

        # weave IP address for container expects a traditional CIDR,
        # e.g. 10.10.10.1/24, hence we return the actual IP and
        # its prefix length
        return str(ip_addr), pool.prefixlen

    def unreserve_ip_addr(self, addr):
        try:
            self.reserved_ip_addrs.remove(addr)
        except ValueError:
            # we don't care about missing element
            pass

    @property
    def ip_addr_available(self):
        """Checks whether there's available IP address in weave network.

        :returns: A boolean represents whether there's available IP address.
        """
        range_size = IPSet(IPNetwork(self.weave_ip_network).iter_hosts()).size
        reserved_size = len(self.reserved_ip_addrs)
        return reserved_size < range_size
