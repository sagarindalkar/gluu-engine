# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel


class OxasimbaNode(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "type",
        "cluster_id",
        "provider_id",
        "ip",
        "name",
        "weave_ip",
        "state",
        "saml_type",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxasimba"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"
        # self.truststore_fn = "/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts"
        # self.ldap_binddn = "cn=directory manager"

    @property
    def recovery_priority(self):
        return 4
