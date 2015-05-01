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
from flask_restful_swagger import swagger
from flask.ext.restful import fields

from gluuapi.model.base import BaseModel
from gluuapi.model.base import HTTPDMixin
from gluuapi.model.base import TomcatMixin


@swagger.model
class oxauthNode(HTTPDMixin, TomcatMixin, BaseModel):
    # Swager Doc
    resource_fields = {
        "id": fields.String(attribute="Node unique identifier"),
        "name": fields.String(attribute="Node name"),
        "type": fields.String(attribute="Node type"),
        "ip": fields.String(attribute="Node IP address"),
        "cluster_id": fields.String(attribute="Cluster ID"),
        "provider_id": fields.String(attribute="Provider ID"),
    }

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxauth"

        self.defaultTrustStoreFN = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'
        self.ldap_binddn = 'cn=directory manager'

        self.openssl_cmd = "/usr/bin/openssl"
        self.keytool_cmd = "/usr/bin/keytool"
        self.cert_folder = "/etc/certs"
        self.oxauth_lib = "/opt/tomcat/webapps/oxauth/WEB-INF/lib"

    @property
    def oxauth_errors_json(self):  # pragma: no cover
        return "gluuapi/templates/salt/oxauth/oxauth-errors.json"

    @property
    def oxauth_ldap_properties(self):  # pragma: no cover
        return "gluuapi/templates/salt/oxauth/oxauth-ldap.properties"

    @property
    def oxauth_config_xml(self):  # pragma: no cover
        return "gluuapi/templates/salt/oxauth/oxauth-config.xml"

    @property
    def oxauth_static_conf_json(self):  # pragma: no cover
        return "gluuapi/templates/salt/oxauth/oxauth-static-conf.json"

    @property
    def oxauth_https_conf(self):  # pragma: no cover
        return "gluuapi/templates/salt/oxauth/oxauth-https.conf"
