# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel


class OxauthNode(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "name",
        "type",
        "ip",
        "cluster_id",
        "provider_id",
        "weave_ip",
        "state",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxauth"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'
        self.ldap_binddn = 'cn=directory manager'

        self.cert_folder = "/etc/certs"
        self.oxauth_lib = "/opt/tomcat/webapps/oxauth/WEB-INF/lib"

        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def recovery_priority(self):
        return 2
