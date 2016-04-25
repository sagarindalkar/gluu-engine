# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from marshmallow import post_load
from marshmallow import validates
from marshmallow import ValidationError
from marshmallow.validate import OneOf

from ..database import db
from ..extensions import ma

#: List of supported container
CONTAINER_CHOICES = [
    "ldap",
    "oxauth",
    "oxtrust",
    "oxidp",
    "nginx",
    # "oxasimba",
]

class ContainerReq(ma.Schema):
    node_id = ma.Str(required=True)

    node_type = ma.Str(validate=OneOf(CONTAINER_CHOICES), required=True)

    # connect_delay = ma.Int(default=10, missing=10,
    #                        error="must use numerical value")
    # exec_delay = ma.Int(default=15, missing=15,
    #                     error="must use numerical value")

    @validates("node_id")
    def validate_node(self, value):
        """Validates node's ID.

        :param value: ID of the node.
        """
        node = db.get(value, "node")
        self.context["node"] = node

        if not node:
            raise ValidationError("invalid node ID")

        if node.type == "worker":
            license_key = db.all("license_keys")[0]
            if license_key.expired:
                raise ValidationError("cannot deploy container to "
                                      "node with expired license")

    @post_load
    def finalize_data(self, data):
        """Build finalized data.
        """
        out = {"params": data}
        out.update({"context": self.context})
        return out
