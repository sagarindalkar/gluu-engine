# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from marshmallow import post_load
from marshmallow import validates
from marshmallow import ValidationError

from ..database import db
from ..extensions import ma

NAME_RE = re.compile('^[a-zA-Z0-9.-]+$')


class NodeReq(ma.Schema):
    name = ma.Str(required=True)
    provider_id = ma.Str(required=True)

    @validates('provider_id')
    def validate_provider(self, value):
        providers = db.search_from_table('providers', {'id': value})
        if not providers:
            raise ValidationError('wrong provider id')

        provider = providers[0]
        if provider.driver == 'generic' and provider.is_in_use():
            raise ValidationError('a generic provider cant be used for more than one node')

    @validates('name')
    def validate_name(self, value):
        if not NAME_RE.match(value):
            raise ValidationError("supported name format is 0-9a-zA-Z.-")

        if db.count_from_table('nodes', {'name': value}):
            raise ValidationError("name is already taken")

    @post_load
    def finalize_data(self, data):
        if self.context["type"] == "discovery":
            data["state_attrs"] = dict.fromkeys([
                "state_node_create",
                "state_install_consul",
                "state_complete",
            ], False)
        if self.context["type"] == "msgcon":
            data["state_attrs"] = dict.fromkeys([
                "state_node_create",
                "state_install_mysql",
                "state_install_activemq",
                "state_install_msgcon",
                "state_pull_images",
                "state_complete",
            ], False)
        elif self.context["type"] == "master":
            data["state_attrs"] = dict.fromkeys([
                "state_node_create",
                "state_complete",
                "state_rng_tools",
                "state_pull_images",
                "state_network_create",
            ], False)
        elif self.context["type"] == "worker":
            data["state_attrs"] = dict.fromkeys([
                "state_node_create",
                "state_complete",
                "state_rng_tools",
                "state_pull_images",
            ], False)
        return data
