import re

from flask_restful import reqparse
from netaddr import AddrFormatError
from netaddr import IPNetwork

# regex pattern to validate email address
EMAIL_RE_ = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def country_code(value, name):
    if len(value) == 2:
        return value
    raise ValueError("The parameter {} requires 2 letters value".format(name))


def admin_email(value, name):
    if EMAIL_RE_.match(value):
        return value
    raise ValueError("The parameter {} is not valid email address".format(name))


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

cluster_req.add_argument("hostname_ldap_cluster", location="form", required=True)
cluster_req.add_argument("hostname_oxauth_cluster", location="form", required=True)
cluster_req.add_argument("hostname_oxtrust_cluster", location="form", required=True)

cluster_req.add_argument("orgName", location="form", required=True)
cluster_req.add_argument("orgShortName", location="form", required=True)
cluster_req.add_argument("countryCode", type=country_code,
                         location="form", required=True)
cluster_req.add_argument("city", location="form", required=True)
cluster_req.add_argument("state", location="form", required=True)
cluster_req.add_argument("admin_email", type=admin_email,
                         location="form", required=True)
cluster_req.add_argument("admin_pw", location="form", required=True)
cluster_req.add_argument("weave_ip_network", type=weave_network_type,
                         location="form", required=True)
