# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel
from ..database import db


class HttpdNode(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "cluster_id",
        "provider_id",
        "ip",
        "weave_ip",
        "name",
        "type",
        "state",
        "oxauth_node_id",
        "oxidp_node_id",
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
        self.type = "httpd"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.httpd_key = "/etc/certs/httpd.key"
        self.httpd_key_orig = "/etc/certs/httpd.key.orig"
        self.httpd_csr = "/etc/certs/httpd.csr"
        self.httpd_crt = "/etc/certs/httpd.crt"
        self.oxauth_node_id = ""
        self.oxidp_node_id = ""

    def get_oxauth_object(self):
        return db.get(self.oxauth_node_id, "nodes")

    @property
    def recovery_priority(self):
        return 4

    def get_oxidp_object(self):
        return db.get(self.oxidp_node_id, "nodes")
