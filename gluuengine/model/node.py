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


class MasterNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_install_weave = BooleanType(default=False)
        state_weave_permission = BooleanType(default=False)
        state_weave_launch = BooleanType(default=False)
        state_docker_cert = BooleanType(default=False)
        state_fswatcher = BooleanType(default=False)
        state_recovery = BooleanType(default=False)
        state_complete = BooleanType(default=False)
        state_rng_tools = BooleanType(default=False)
        state_pull_images = BooleanType(default=False)
        state_registry_cert = BooleanType(default=False)

    id = StringType(default=str(uuid.uuid4()))
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
            "state_install_weave": self.state_install_weave,
            "state_weave_permission": self.state_weave_permission,
            "state_weave_launch": self.state_weave_launch,
            "state_docker_cert": self.state_docker_cert,
            "state_fswatcher": self.state_fswatcher,
            "state_recovery": self.state_recovery,
            "state_complete": self.state_complete,
            "state_rng_tools": self.state_rng_tools,
            "state_pull_images": self.state_pull_images,
            # "state_registry_cert": self.state_registry_cert,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_install_weave(self):
        return self._resolve_state_attr("state_install_weave")

    @property
    def state_weave_permission(self):
        return self._resolve_state_attr("state_weave_permission")

    @property
    def state_weave_launch(self):
        return self._resolve_state_attr("state_weave_launch")

    @property
    def state_docker_cert(self):
        return self._resolve_state_attr("state_docker_cert")

    @property
    def state_fswatcher(self):
        return self._resolve_state_attr("state_fswatcher")

    @property
    def state_recovery(self):
        return self._resolve_state_attr("state_recovery")

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
    def state_registry_cert(self):
        return self._resolve_state_attr("state_registry_cert")


class WorkerNode(Node):
    class StateAttrs(BaseModel):
        state_node_create = BooleanType(default=False)
        state_install_weave = BooleanType(default=False)
        state_weave_permission = BooleanType(default=False)
        state_weave_launch = BooleanType(default=False)
        state_recovery = BooleanType(default=False)
        state_complete = BooleanType(default=False)
        state_rng_tools = BooleanType(default=False)
        state_pull_images = BooleanType(default=False)
        state_registry_cert = BooleanType(default=False)

    id = StringType(default=str(uuid.uuid4()))
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
            "state_install_weave": self.state_install_weave,
            "state_weave_permission": self.state_weave_permission,
            "state_weave_launch": self.state_weave_launch,
            "state_recovery": self.state_recovery,
            "state_complete": self.state_complete,
            "state_rng_tools": self.state_rng_tools,
            "state_pull_images": self.state_pull_images,
            # "state_registry_cert": self.state_registry_cert,
        }

    @property
    def state_node_create(self):
        return self._resolve_state_attr("state_node_create")

    @property
    def state_install_weave(self):
        return self._resolve_state_attr("state_install_weave")

    @property
    def state_weave_permission(self):
        return self._resolve_state_attr("state_weave_permission")

    @property
    def state_weave_launch(self):
        return self._resolve_state_attr("state_weave_launch")

    @property
    def state_recovery(self):
        return self._resolve_state_attr("state_recovery")

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
    def state_registry_cert(self):
        return self._resolve_state_attr("state_registry_cert")
