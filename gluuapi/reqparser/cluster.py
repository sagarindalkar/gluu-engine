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
# import re

from flask_restful import reqparse
from netaddr import AddrFormatError
from netaddr import IPNetwork

# backward-compat
from gluuapi.reqparser.base import email_type as admin_email


def country_code(value, name):
    if len(value) == 2:
        return value
    raise ValueError("The parameter {} requires 2 letters value".format(name))


def weave_network_type(value, name):
    # checks whether IP network is valid
    try:
        IPNetwork(value)
    except AddrFormatError:
        raise ValueError(
            "{} is not valid value for parameter {}".format(value, name))
    return value


# Request parser for cluster POST request
cluster_req = reqparse.RequestParser()

cluster_req.add_argument("name", location="form", required=True)
cluster_req.add_argument("description", location="form")
cluster_req.add_argument("ox_cluster_hostname", location="form", required=True)
cluster_req.add_argument("org_name", location="form", required=True)
cluster_req.add_argument("org_short_name", location="form", required=True)
cluster_req.add_argument("country_code", type=country_code,
                         location="form", required=True)
cluster_req.add_argument("city", location="form", required=True)
cluster_req.add_argument("state", location="form", required=True)
cluster_req.add_argument("admin_email", type=admin_email,
                         location="form", required=True)
cluster_req.add_argument("admin_pw", location="form", required=True)
cluster_req.add_argument("weave_ip_network", type=weave_network_type,
                         location="form", required=True)
