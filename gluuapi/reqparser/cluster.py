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
import re

from marshmallow import validates
from marshmallow import ValidationError
from netaddr import AddrFormatError
from netaddr import IPNetwork

from gluuapi.extensions import ma

WEAVE_NETWORK_RE = re.compile(
    r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}"
)


class ClusterReq(ma.Schema):
    name = ma.Str(required=True)
    description = ma.Str()
    ox_cluster_hostname = ma.Str(required=True)
    org_name = ma.Str(required=True)
    org_short_name = ma.Str(required=True)
    country_code = ma.Str(required=True)
    city = ma.Str(required=True)
    state = ma.Str(required=True)
    admin_email = ma.Email(required=True)
    admin_pw = ma.Str(required=True)
    weave_ip_network = ma.Str(required=True)

    @validates("country_code")
    def validate_country_code(self, value):
        if len(value) != 2:
            raise ValidationError("requires 2 characters")

    @validates("weave_ip_network")
    def validate_weave_ip_network(self, value):
        # allow only IPv4 for now
        if not WEAVE_NETWORK_RE.match(value):
            raise ValidationError("invalid IP network address format")

        # check if IP is supported by ``netaddr``
        try:
            IPNetwork(value)
        except AddrFormatError as exc:
            raise ValidationError(exc.message)

    @validates("admin_pw")
    def validate_admin_pw(self, value):
        if len(value) < 6:
            raise ValidationError("Must use at least 6 characters")
