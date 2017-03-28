# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from marshmallow import validates
from marshmallow import ValidationError

from ..extensions import ma
from ..model import Provider
from ..model import Node

NAME_RE = re.compile('^[a-zA-Z0-9.-]+$')


class NodeReq(ma.Schema):
    name = ma.Str(required=True)
    provider_id = ma.Str(required=True)

    @validates('provider_id')
    def validate_provider(self, value):
        provider = Provider.query.get(value)
        if not provider:
            raise ValidationError('wrong provider id')

        if provider.driver == 'generic' and provider.is_in_use():
            raise ValidationError('a generic provider cant be used for more than one node')

    @validates('name')
    def validate_name(self, value):
        if not NAME_RE.match(value):
            raise ValidationError("supported name format is 0-9a-zA-Z.-")

        if Node.query.filter_by(name=value).count():
            raise ValidationError("name is already taken")
