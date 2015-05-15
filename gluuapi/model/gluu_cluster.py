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
from flask_restful.fields import String
from netaddr import IPNetwork
from netaddr import IPSet

from gluuapi.database import db
from gluuapi.model.base import BaseModel
from gluuapi.utils import get_quad
from gluuapi.utils import get_random_chars
from gluuapi.utils import encrypt_text
from gluuapi.utils import decrypt_text
from gluuapi.utils import generate_passkey
from gluuapi.utils import ldap_encode


@swagger.model
class GluuCluster(BaseModel):
    # Swager Doc
    resource_fields = {
        'id': String(attribute='GluuCluster unique identifier'),
        'name': String(attribute='GluuCluster name'),
        'description': String(attribute='Description of cluster'),
        'ox_cluster_hostname': String,
        'ldaps_port': String,
        'org_name': String(attribute='Name of org for X.509 certificate'),  # noqa
        'org_short_name': String(attribute='Short name of org for X.509 certificate'),  # noqa
        'country_code': String(attribute='ISO 3166-1 alpha-2 country code'),  # noqa
        'city': String(attribute='City for X.509 certificate'),
        'state': String(attribute='State or province for X.509 certificate'),  # noqa
        'admin_email': String(attribute='Admin email address for X.509 certificate'),  # noqa
        'base_inum': String(attribute='Unique identifier for domain'),
        'inum_org': String(attribute='Unique identifier for organization'),  # noqa
        'inum_org_fn': String(attribute='Unique organization identifier sans special characters.'),  # noqa
        'inum_appliance': String(attribute='Unique identifier for cluster'),  # noqa
        'inum_appliance_fn': String(attribute='Unique cluster identifier sans special characters.'),  # noqa
        'weave_ip_network': String(attribute='Weave IP network'),  # noqa
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
        self.httpd_nodes = []
        self.ox_cluster_hostname = fields.get("ox_cluster_hostname")
        self.ldaps_port = "1636"

        # X.509 Certificate Information
        self.org_name = fields.get("org_name")
        self.org_short_name = fields.get("org_short_name")
        self.country_code = fields.get("country_code")
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
        self.base_inum = '@!%s.%s.%s.%s' % tuple([get_quad() for i in xrange(4)])

        org_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inum_org = '%s!0001!%s' % (self.base_inum, org_quads)

        appliance_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.inum_appliance = '%s!0002!%s' % (self.base_inum, appliance_quads)

        self.inum_org_fn = self.inum_org.replace('@', '').replace('!', '').replace('.', '')
        self.inum_appliance_fn = self.inum_appliance.replace('@', '').replace('!', '').replace('.', '')

        # ox-related attrs
        client_quads = '%s.%s' % tuple([get_quad() for i in xrange(2)])
        self.oxauth_client_id = '%s!0008!%s' % (self.base_inum, client_quads)
        oxauth_client_pw = get_random_chars()
        self.oxauth_client_encoded_pw = encrypt_text(oxauth_client_pw, self.passkey)

        # key store
        self.encoded_shib_jks_pw = self.admin_pw
        self.shib_jks_fn = "/etc/certs/shibIDP.jks"
        self.weave_ip_network = fields.get("weave_ip_network", "10.2.1.0/24")
        self.reserved_ip_addrs = []

    @property
    def decrypted_admin_pw(self):
        return decrypt_text(self.admin_pw, self.passkey)

    @property
    def max_allowed_ldap_nodes(self):
        return 4

    def get_ldap_objects(self):
        """Get available ldap objects (models).
        """
        return self.get_node_objects(type_="ldap")

    def get_oxauth_objects(self):
        """Get available oxAuth objects (models).
        """
        return self.get_node_objects(type_="oxauth")

    def get_oxtrust_objects(self):
        """Get available oxTrust objects (models).
        """
        return self.get_node_objects(type_="oxtrust")

    def get_httpd_objects(self):
        """Get available httpd objects (models).
        """
        return self.get_node_objects(type_="httpd")

    def get_node_objects(self, type_=""):
        condition = db.where("cluster_id") == self.id
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.search_from_table("nodes", condition)

    @property
    def exposed_weave_ip(self):
        pool = IPNetwork(self.weave_ip_network)
        # get the last element of host IP address
        addr = list(itertools.islice(pool.iter_hosts(), pool.size - 3, pool.size))[0]
        return str(addr), pool.prefixlen

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

        # a generator holds possible IP addresses range, excluding exposed weave IP
        ip_range = IPSet(pool.iter_hosts()) ^ IPSet(self.reserved_ip_addrs) ^ IPSet([self.exposed_weave_ip[0]])

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
        exposed_ip_len = 1
        return reserved_size + exposed_ip_len < range_size
