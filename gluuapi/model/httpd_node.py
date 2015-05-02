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
from flask_restful import fields as rest_fields
from flask_restful_swagger import swagger

from gluuapi.model.base import BaseModel


@swagger.model
class HttpdNode(BaseModel):
    resource_fields = {
        "id": rest_fields.String,
        "cluster_id": rest_fields.String,
        "provider_id": rest_fields.String,
        "ip": rest_fields.String,
        "weave_ip": rest_fields.String,
        "name": rest_fields.String,
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

    @property
    def https_conf(self):
        return "gluuapi/templates/salt/httpd/gluu_https.conf"
