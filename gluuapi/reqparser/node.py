# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from marshmallow import post_load
from marshmallow import validates
from marshmallow import ValidationError

from ..database import db
from ..extensions import ma

#: List of supported nodes
NODE_CHOICES = [
    "ldap",
    "oxauth",
    "oxtrust",
    "oxidp",
    "nginx",
    "oxasimba",
]

class NodeReq(ma.Schema):
    cluster_id = ma.Str(required=True)
    provider_id = ma.Str(required=True)

    try:
        node_type = ma.Select(choices=NODE_CHOICES, required=True)
    except AttributeError:  # pragma: no cover
        # marshmallow.Select is removed starting from 2.0.0
        from marshmallow.validate import OneOf
        node_type = ma.Str(validate=OneOf(NODE_CHOICES), required=True)

    connect_delay = ma.Int(default=10, missing=10,
                           error="must use numerical value")
    exec_delay = ma.Int(default=15, missing=15,
                        error="must use numerical value")

    @validates("cluster_id")
    def validate_cluster(self, value):
        """Validates cluster's ID.

        :param value: ID of the cluster.
        """
        cluster = db.get(value, "clusters")
        self.context["cluster"] = cluster
        if not cluster:
            raise ValidationError("invalid cluster ID")

    @validates("provider_id")
    def validate_provider(self, value):
        """Validates provider's ID.

        :param value: ID of the provider.
        """
        provider = db.get(value, "providers")
        self.context["provider"] = provider

        if not provider:
            raise ValidationError("invalid provider ID")
        if provider.type == "consumer":
            license_key = db.all("license_keys")[0]
            if license_key.expired:
                raise ValidationError("cannot deploy node to "
                                      "provider with expired license")

    @post_load
    def finalize_data(self, data):
        """Build finalized data.
        """
        out = {"params": data}
        out.update({"context": self.context})
        return out
