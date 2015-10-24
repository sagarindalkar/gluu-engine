# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask_restful.fields import String
from flask_restful_swagger import swagger

from .base import BaseModel
from ..database import db


@swagger.model
class HttpdNode(BaseModel):
    resource_fields = {
        "id": String,
        "cluster_id": String,
        "provider_id": String,
        "ip": String,
        "weave_ip": String,
        "name": String,
        "type": String,
        "state": String,
        "oxauth_node_id": String,
        "saml_node_id": String,
        "domain_name": String,
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
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.httpd_key = "/etc/certs/httpd.key"
        self.httpd_key_orig = "/etc/certs/httpd.key.orig"
        self.httpd_csr = "/etc/certs/httpd.csr"
        self.httpd_crt = "/etc/certs/httpd.crt"
        self.oxauth_node_id = ""
        self.saml_node_id = ""

    def get_oxauth_object(self):
        return db.get(self.oxauth_node_id, "nodes")

    @property
    def recovery_priority(self):
        return 4

    def get_saml_object(self):
        return db.get(self.saml_node_id, "nodes")
