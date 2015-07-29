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
import uuid

from flask_restful_swagger import swagger
from flask_restful.fields import String
from netaddr import IPNetwork
from netaddr import IPAddress

from gluuapi.database import db
from gluuapi.model.base import BaseModel
from gluuapi.model.base import STATE_SUCCESS
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
        # hence we fetch the last element before broadcast address
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

        if not self.last_fetched_addr:
            # import from reserved_ip_addrs for backward-compat
            try:
                self.last_fetched_addr = self.reserved_ip_addrs[-1]
            except IndexError:
                pass

        if self.last_fetched_addr:
            addr = str(IPAddress(self.last_fetched_addr) + 1)
        else:
            # skips ``pool.network`` address
            addr = str(pool[1])

        if addr in (self.exposed_weave_ip[0], str(pool.network),
                    str(pool.broadcast)):
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
