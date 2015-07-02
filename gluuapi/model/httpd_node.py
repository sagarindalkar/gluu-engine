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
from flask_restful.fields import String
from flask_restful_swagger import swagger

from gluuapi.model.base import BaseModel
from gluuapi.database import db


@swagger.model
class HttpdNode(BaseModel):
    resource_fields = {
        "id": String,
        "cluster_id": String,
        "provider_id": String,
        "ip": String,
        "weave_ip": String,
        "name": String,
        "type": String,
        "state": String,
        "oxauth_node_id": String,
        "oxtrust_node_id": String,
    }

    def __init__(self):
        self.id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.type = "httpd"
        self.state = ""

        self.cert_folder = "/etc/certs"
        self.httpd_key = "/etc/certs/httpd.key"
        self.httpd_key_orig = "/etc/certs/httpd.key.orig"
        self.httpd_csr = "/etc/certs/httpd.csr"
        self.httpd_crt = "/etc/certs/httpd.crt"
        self.oxauth_node_id = ""
        self.oxtrust_node_id = ""

    def get_oxauth_object(self):
        return db.get(self.oxauth_node_id, "nodes")

    def get_oxtrust_object(self):
        return db.get(self.oxtrust_node_id, "nodes")
