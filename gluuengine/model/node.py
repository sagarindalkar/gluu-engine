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

    # def __init__(self, fields=None):  # pragma: no cover
    #     self.id = str(uuid.uuid4())
    #     self.populate(fields)

    # def populate(self, fields=None):  # pragma: no cover
    #     fields = fields or {}
    #     self.name = fields.get('name', '')
    #     self.type = fields.get('type', '')
    #     self.provider_id = fields.get('provider_id', '')
    #     #self.provider_type = fields.get('provider_type', '')

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


class DiscoveryNode(Node):
    state_fields = dict.fromkeys([
        'state_node_create',
        'state_install_consul',
        'state_complete'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.state_node_create = False
        self.state_install_consul = False
        self.state_complete = False
        self.type = 'discovery'
        self.populate(fields)
        self.resource_fields = dict(self.resource_fields.items() + self.state_fields.items())

    def populate(self, fields=None):
        fields = fields or {}
        self.name = 'gluu.discovery'
        #self.type = fields.get('type', '')
        self.provider_id = fields.get('provider_id', '')


class MasterNode(Node):
    state_fields = dict.fromkeys([
        'state_node_create',
        'state_install_weave',
        'state_weave_permission',
        'state_weave_launch',
        'state_registry_cert',
        'state_docker_cert',
        'state_fswatcher',
        'state_recovery',
        'state_complete'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.state_node_create = False
        self.state_install_weave = False
        self.state_weave_permission = False
        self.state_weave_launch = False
        self.state_registry_cert = False
        self.state_docker_cert = False
        self.state_fswatcher = False
        self.state_recovery = False
        self.state_complete = False
        self.type = 'master'
        self.populate(fields)
        self.resource_fields = dict(self.resource_fields.items() + self.state_fields.items())

    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        #self.type = fields.get('type', '')
        self.provider_id = fields.get('provider_id', '')

class WorkerNode(Node):
    state_fields = dict.fromkeys([
        'state_node_create',
        'state_install_weave',
        'state_weave_permission',
        'state_weave_launch',
        'state_registry_cert',
        'state_recovery',
        'state_complete'
    ])

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.state_node_create = False
        self.state_install_weave = False
        self.state_weave_permission = False
        self.state_weave_launch = False
        self.state_registry_cert = False
        self.state_recovery = False
        self.state_complete = False
        self.type = 'worker'
        self.populate(fields)
        self.resource_fields = dict(self.resource_fields.items() + self.state_fields.items())

    def populate(self, fields=None):
        fields = fields or {}
        self.name = fields.get('name', '')
        #self.type = fields.get('type', '')
        self.provider_id = fields.get('provider_id', '')
