# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from marshmallow import post_load
from marshmallow import validates
from marshmallow import validates_schema
from marshmallow import ValidationError

from gluuapi.database import db
from gluuapi.extensions import ma
from gluuapi.model import STATE_SUCCESS

NODE_CHOICES = ["ldap", "oxauth", "oxtrust", "httpd"]


class NodeReq(ma.Schema):
    cluster_id = ma.Str(required=True)
    provider_id = ma.Str(required=True)
    node_type = ma.Select(choices=NODE_CHOICES, error="unsupported type")
    connect_delay = ma.Int(default=10, missing=10,
                           error="must use numerical value")
    exec_delay = ma.Int(default=15, missing=15,
                        error="must use numerical value")
    oxauth_node_id = ma.Str(default="", missing="")
    oxtrust_node_id = ma.Str(default="", missing="")

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
            data.pop("oxtrust_node_id", None)

        out = {"params": data}
        out.update({"context": self.context})
        return out

    @validates_schema
    def validate_schema(self, data):
        self.validate_oxauth(data.get("oxauth_node_id"))
        self.validate_oxtrust(data.get("oxtrust_node_id"))

    def validate_oxauth(self, value):
        if self.context.get("node_type") == "httpd":
            node_in_use = db.count_from_table(
                "nodes",
                db.where("oxauth_node_id") == value,
            )
            if node_in_use:
                raise ValidationError("cannot reuse the oxAuth node",
                                      "oxauth_node_id")

            try:
                node = db.search_from_table(
                    "nodes",
                    (db.where("id") == value) & (db.where("type") == "oxauth")
                )[0]
            except IndexError:
                node = None

            if not node:
                raise ValidationError("invalid oxAuth node",
                                      "oxauth_node_id")

            if node.provider_id != self.context["provider"].id:
                raise ValidationError(
                    "only oxAuth node within same provider is allowed",
                    "oxauth_node_id",
                )

            if node.state != STATE_SUCCESS:
                raise ValidationError(
                    "only oxAuth node with SUCCESS state is allowed",
                    "oxauth_node_id",
                )

    def validate_oxtrust(self, value):
        if self.context.get("node_type") == "httpd":
            node_in_use = db.count_from_table(
                "nodes",
                db.where("oxtrust_node_id") == value,
            )
            if node_in_use:
                raise ValidationError("cannot reuse the oxTrust node",
                                      "oxtrust_node_id")

            try:
                node = db.search_from_table(
                    "nodes",
                    (db.where("id") == value) & (db.where("type") == "oxtrust")
                )[0]
            except IndexError:
                node = None

            if not node:
                raise ValidationError("invalid oxTrust node",
                                      "oxtrust_node_id")

            if node.provider_id != self.context["provider"].id:
                raise ValidationError(
                    "only oxTrust node within same provider is allowed",
                    "oxtrust_node_id",
                )

            if node.state != STATE_SUCCESS:
                raise ValidationError(
                    "only oxTrust node with SUCCESS state is allowed",
                    "oxtrust_node_id",
                )
