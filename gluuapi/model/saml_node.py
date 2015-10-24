# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask_restful.fields import String
from flask_restful_swagger import swagger

from .base import BaseModel


@swagger.model
class SamlNode(BaseModel):
    resource_fields = {
        "id": String,
        "type": String,
        "cluster_id": String,
        "provider_id": String,
        "ip": String,
        "name": String,
        "weave_ip": String,
        "state": String,
        "saml_type": String,
        "domain_name": String,
    }

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "saml"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"
        self.truststore_fn = "/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts"
        self.ldap_binddn = "cn=directory manager"
        self.saml_type = "shibboleth"

    @property
    def recovery_priority(self):
        return 4
