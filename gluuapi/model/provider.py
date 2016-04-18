# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from ..database import db
from .base import BaseModel


class GenericProvider(BaseModel):
    resource_fields = dict.fromkeys([
        'id',
        'name',
        'driver',
        'generic_ip_address',
        'generic_ssh_key',
        'generic_ssh_user',
        'generic_ssh_port'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.driver = 'generic'
        self.populate(fields)


    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        self.generic_ip_address = fields.get('generic_ip_address', '')
        self.generic_ssh_key = fields.get('generic_ssh_key', '')
        self.generic_ssh_user = fields.get('generic_ssh_user', '')
        self.generic_ssh_port = fields.get('generic_ssh_port', '')


    def is_in_use():
        condition = db.where("provider_id") == self.uid
        return db.count_from_table("nodes", condition)


class Aws(BaseModel):
    pass


class Do(BaseModel):
    pass 
