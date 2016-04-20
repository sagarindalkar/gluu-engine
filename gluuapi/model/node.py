# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

#{
#    "provider_id": "<id>",
#    "provider_type": "",
#    "name": "<>",
#    "type": "<master|worker|keystore>",
#}

# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from .base import BaseModel
from ..database import db


class Node(BaseModel):
    resource_fields = dict.fromkeys([
        'id',
        'name',
        'type',
        'provider_id',
        #'provider_type'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.populate(fields)

    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        self.type = fields.get('type', '')
        self.provider_id = fields.get('provider_id', '')
        #self.provider_type = fields.get('provider_type', '')



