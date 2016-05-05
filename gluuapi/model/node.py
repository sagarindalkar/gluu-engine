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
from .base import STATE_SUCCESS
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

    def count_containers(self, type_="", state=STATE_SUCCESS):
        """Counts available containers objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = db.where("node_id") == self.id
        if state:
            condition = (condition) & (db.where("state") == state)
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.count_from_table("containers", condition)

    def get_containers(self, type_="", state=STATE_SUCCESS):
        """Gets available container objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = db.where("node_id") == self.id
        if state:
            condition = (condition) & (db.where("state") == state)
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.search_from_table("containers", condition)


class Discovery(Node):
    pass

class Master(Node):
    pass

class Worker(Node):
    pass
