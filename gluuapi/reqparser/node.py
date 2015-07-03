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
from marshmallow import ValidationError

from gluuapi.database import db
from gluuapi.extensions import ma

NODE_CHOICES = ["ldap", "oxauth", "oxtrust", "httpd"]


class NodeReq(ma.Schema):
    cluster_id = ma.Str(required=True)
    provider_id = ma.Str(required=True)
    node_type = ma.Select(choices=NODE_CHOICES, error="unsupported type")
    connect_delay = ma.Int(default=10, missing=10,
                           error="must use numerical value")
    exec_delay = ma.Int(default=15, missing=15,
                        error="must use numerical value")

    @validates("cluster_id")
    def validate_cluster(self, value):
        cluster = db.get(value, "clusters")
        self.context["cluster"] = cluster
        if not cluster:
            raise ValidationError("invalid cluster ID")
        if not cluster.ip_addr_available:
            raise ValidationError("cluster is running out of weave IP")

    @validates("provider_id")
    def validate_provider(self, value):
        provider = db.get(value, "providers")
        self.context["provider"] = provider
        if not provider:
            raise ValidationError("invalid provider ID")
        if provider.type == "consumer":
            license = db.get(provider.license_id, "licenses")
            if license and license.expired:
                raise ValidationError("cannot deploy node to "
                                      "provider with expired license")

    @validates("node_type")
    def validate_node(self, value):
        cluster = self.context.get("cluster")
        if value == "ldap" and cluster is not None:
            max_num = cluster.max_allowed_ldap_nodes
            if len(cluster.get_ldap_objects()) >= max_num:
                raise ValidationError("max. allowed LDAP nodes is exceeded")

    @post_load
    def finalize_data(self, data):
        out = {"params": data}
        out.update({"context": self.context})
        return out
