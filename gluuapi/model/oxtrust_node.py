# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel


class OxtrustNode(BaseModel):
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
        self.hostname = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxtrust"
        self.image = "gluuoxtrust"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.ldap_binddn = 'cn=directory manager'
        self.cert_folder = "/etc/certs"
        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'

        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 5
