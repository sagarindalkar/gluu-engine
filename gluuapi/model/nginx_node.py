# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel


class NginxNode(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "cluster_id",
        "provider_id",
        "ip",
        "weave_ip",
        "name",
        "type",
        "state",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.cluster_id = ""
        self.provider_id = ""
        self.type = "nginx"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.domain_name = ""
        self.cert_folder = "/etc/certs"

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 4
