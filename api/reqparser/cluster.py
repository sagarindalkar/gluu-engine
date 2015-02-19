from flask.ext.restful import reqparse

# Request parser for cluster POST and PUT requests
cluster_reqparser = reqparse.RequestParser()
cluster_reqparser.add_argument("name", type=str)
cluster_reqparser.add_argument("description", type=str)
cluster_reqparser.add_argument("hostname_ldap_cluster", type=str)
cluster_reqparser.add_argument("hostname_oxauth_cluster", type=str)
cluster_reqparser.add_argument("hostname_oxtrust_cluster", type=str)
cluster_reqparser.add_argument("hostname_oxtrust_cluster", type=str)
cluster_reqparser.add_argument("orgName", type=str)
cluster_reqparser.add_argument("orgShortName", type=str)
cluster_reqparser.add_argument("countryCode", type=str)
cluster_reqparser.add_argument("city", type=str)
cluster_reqparser.add_argument("state", type=str)
cluster_reqparser.add_argument("admin_email", type=str)
# cluster_reqparser.add_argument("encoded_ox_ldap_pw", type=str)
# cluster_reqparser.add_argument("encoded_ldap_pw", type=str)
cluster_reqparser.add_argument("baseInum", type=str)
cluster_reqparser.add_argument("inumOrg", type=str)
cluster_reqparser.add_argument("inumOrgFN", type=str)
cluster_reqparser.add_argument("inumAppliance", type=str)
cluster_reqparser.add_argument("inumApplianceFN", type=str)
