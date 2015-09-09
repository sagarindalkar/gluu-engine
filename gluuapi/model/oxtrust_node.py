# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask_restful.fields import String
from flask_restful_swagger import swagger

from .base import BaseModel


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
        return 4
