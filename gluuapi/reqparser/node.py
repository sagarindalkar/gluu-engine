# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from marshmallow import post_load
from marshmallow import validates
from marshmallow import validates_schema
from marshmallow import ValidationError

from ..database import db
from ..extensions import ma
from ..model import STATE_SUCCESS

NODE_CHOICES = ["ldap", "oxauth", "oxtrust", "httpd", "oxidp"]


class NodeReq(ma.Schema):
    cluster_id = ma.Str(required=True)
    provider_id = ma.Str(required=True)

    try:
        node_type = ma.Select(choices=NODE_CHOICES, required=True)
    except AttributeError:
        # marshmallow.Select is removed starting from 2.0.0
        from marshmallow.validate import OneOf
        node_type = ma.Str(validate=OneOf(NODE_CHOICES), required=True)

    connect_delay = ma.Int(default=10, missing=10,
                           error="must use numerical value")
    exec_delay = ma.Int(default=15, missing=15,
                        error="must use numerical value")
    oxauth_node_id = ma.Str(default="", missing="")
    oxidp_node_id = ma.Str(default="", missing="")

    @validates("cluster_id")
    def validate_cluster(self, value):
        cluster = db.get(value, "clusters")
        self.context["cluster"] = cluster
        if not cluster:
            raise ValidationError("invalid cluster ID")

        addr, _ = cluster.reserve_ip_addr()
        if not addr:
            raise ValidationError("cluster is running out of weave IP")

    @validates("provider_id")
    def validate_provider(self, value):
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
        if data.get("node_type") != "httpd":
            data.pop("oxauth_node_id", None)
            data.pop("oxidp_node_id", None)

        out = {"params": data}
        out.update({"context": self.context})
        return out

    @validates_schema
    def validate_schema(self, data):
        if self.context.get("node_type") == "httpd":
            oxauth_node_id = data.get("oxauth_node_id")
            self.validate_oxauth(oxauth_node_id)

            oxidp_node_id = data.get("oxidp_node_id")
            if oxidp_node_id:
                self.validate_oxidp(oxidp_node_id)

    def validate_oxauth(self, value):
        node_in_use = db.count_from_table(
            "nodes",
            db.where("oxauth_node_id") == value,
        )
        if node_in_use:
            raise ValidationError("cannot reuse the oxauth node",
                                  "oxauth_node_id")

        try:
            node = db.search_from_table(
                "nodes",
                (db.where("id") == value) & (db.where("type") == "oxauth")
            )[0]
        except IndexError:
            node = None

        if not node:
            raise ValidationError("invalid oxauth node",
                                  "oxauth_node_id")

        if node.provider_id != self.context["provider"].id:
            raise ValidationError(
                "only oxauth node within same provider is allowed",
                "oxauth_node_id",
            )

        if node.state != STATE_SUCCESS:
            raise ValidationError(
                "only oxauth node with SUCCESS state is allowed",
                "oxauth_node_id",
            )

    def validate_oxidp(self, value):
        node_in_use = db.count_from_table(
            "nodes",
            db.where("oxidp_node_id") == value,
        )
        if node_in_use:
            raise ValidationError("cannot reuse the oxidp node",
                                  "oxidp_node_id")

        try:
            node = db.search_from_table(
                "nodes",
                (db.where("id") == value) & (db.where("type") == "oxidp")
            )[0]
        except IndexError:
            node = None

        if not node:
            raise ValidationError("invalid oxidp node",
                                  "oxidp_node_id")

        if node.provider_id != self.context["provider"].id:
            raise ValidationError(
                "only oxidp node within same provider is allowed",
                "oxidp_node_id",
            )

        if node.state != STATE_SUCCESS:
            raise ValidationError(
                "only oxidp node with SUCCESS state is allowed",
                "oxidp_node_id",
            )
