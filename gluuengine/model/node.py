# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from schematics.types import BooleanType
from schematics.types import StringType
from schematics.types.compound import PolyModelType

from ._schema import NODE_SCHEMA
from .base import BaseModel
from .base import STATE_SUCCESS
from ..database import db


class Node(BaseModel):
    @property
    def _schema(self):
        return NODE_SCHEMA

    def count_containers(self, type_="", state=STATE_SUCCESS):
        """Counts available containers objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = {"node_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return db.count_from_table("containers", condition)

    def get_containers(self, type_="", state=STATE_SUCCESS):
        """Gets available container objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = {"node_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return db.search_from_table("containers", condition)

    def _resolve_state_attr(self, field):
        try:
            return self.state_attrs.get(field)
        except (AttributeError, TypeError,):
            return self._initial.get(field)


class DiscoveryNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_install_consul = BooleanType(default=False)
        state_complete = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    provider_id = StringType()
    type = StringType(default="discovery")
    state_attrs = PolyModelType(StateAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "provider_id": self.provider_id,
            "state_node_create": self.state_node_create,
            "state_install_consul": self.state_install_consul,
            "state_complete": self.state_complete,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_install_consul(self):
        return self._resolve_state_attr("state_install_consul")

    @property
    def state_complete(self):
        return self._resolve_state_attr("state_complete")


class MsgconNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_install_mysql= BooleanType(default=False)
        state_install_activemq = BooleanType(default=False)
        state_install_msgcon = BooleanType(default=False)
        state_pull_images = BooleanType(default=False)
        state_complete = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    provider_id = StringType()
    type = StringType(default="msgcon")
    state_attrs = PolyModelType(StateAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "provider_id": self.provider_id,
            "state_node_create": self.state_node_create,
            "state_install_mysql": self.state_install_mysql,
            "state_install_activemq": self.state_install_activemq,
            "state_install_msgcon": self.state_install_msgcon,
            "state_pull_images": self.state_pull_images,
            "state_complete": self.state_complete,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_install_mysql(self):
        return self._resolve_state_attr("state_install_mysql")

    @property
    def state_install_activemq(self):
        return self._resolve_state_attr("state_install_activemq")

    @property
    def state_install_msgcon(self):
        return self._resolve_state_attr("state_install_msgcon")

    @property
    def state_pull_images(self):
        return self._resolve_state_attr("state_pull_images")

    @property
    def state_complete(self):
        return self._resolve_state_attr("state_complete")


class MasterNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_complete = BooleanType(default=False)
        state_rng_tools = BooleanType(default=False)
        state_pull_images = BooleanType(default=False)
        state_network_create = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    provider_id = StringType()
    type = StringType(default="master")
    state_attrs = PolyModelType(StateAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "provider_id": self.provider_id,
            "state_node_create": self.state_node_create,
            "state_complete": self.state_complete,
            "state_rng_tools": self.state_rng_tools,
            "state_pull_images": self.state_pull_images,
            "state_network_create": self.state_network_create,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_complete(self):
        return self._resolve_state_attr("state_complete")

    @property
    def state_rng_tools(self):
        return self._resolve_state_attr("state_rng_tools")

    @property
    def state_pull_images(self):
        return self._resolve_state_attr("state_pull_images")

    @property
    def state_network_create(self):
        return self._resolve_state_attr("state_network_create")


class WorkerNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_complete = BooleanType(default=False)
        state_rng_tools = BooleanType(default=False)
        state_pull_images = BooleanType(default=False)

    id = StringType(default=lambda: str(uuid.uuid4()))
    name = StringType()
    provider_id = StringType()
    type = StringType(default="worker")
    state_attrs = PolyModelType(StateAttrs, strict=False)
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "provider_id": self.provider_id,
            "state_node_create": self.state_node_create,
            "state_complete": self.state_complete,
            "state_rng_tools": self.state_rng_tools,
            "state_pull_images": self.state_pull_images,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_complete(self):
        return self._resolve_state_attr("state_complete")

    @property
    def state_rng_tools(self):
        return self._resolve_state_attr("state_rng_tools")

    @property
    def state_pull_images(self):
        return self._resolve_state_attr("state_pull_images")
