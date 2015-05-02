from flask.ext.restful import reqparse

node_req = reqparse.RequestParser()
node_req.add_argument("cluster", location="form", required=True,
                      help="Cluster ID to which this node will be added")
node_req.add_argument("node_type", location="form", required=True,
                      choices=["ldap", "oxauth", "oxtrust", "httpd"],
                      help="one of 'ldap', 'oxauth', 'oxtrust', or 'httpd'")
node_req.add_argument("provider_id", location="form", required=True,
                      help="Provider ID to which this node will be added")
