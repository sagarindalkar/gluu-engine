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


@swagger.model
class OxtrustNode(BaseModel):
    # Swager Doc
    resource_fields = {
        "id": String(attribute="Node unique identifier"),
        "name": String(attribute="Node name"),
        "type": String(attribute="Node type"),
        "ip": String(attribute="Node IP address"),
        "cluster_id": String(attribute="Cluster ID"),
        "provider_id": String(attribute="Provider ID"),
        "weave_ip": String,
        "state": String,
    }

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.name = ""
        self.hostname = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxtrust"
        self.state = ""
        self.setup_logpath = ""

        self.ldap_binddn = 'cn=directory manager'
        self.cert_folder = "/etc/certs"
        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'

        # enabled if we have saml
        self.oxtrust_config_generation = "disabled"

        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def recovery_priority(self):
        return 3
