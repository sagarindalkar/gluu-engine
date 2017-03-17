# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from sqlalchemy import JSON

from .base import STATE_SUCCESS
from .container import Container
from ..database import db


class Node(db.Model):
    __tablename__ = "nodes"

    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    name = db.Column(db.Unicode(36))
    provider_id = db.Column(db.Unicode(36))
    type = db.Column(db.Unicode(32))
    state_attrs = db.Column(JSON)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "node",
    }

    def count_containers(self, type_="", state=STATE_SUCCESS):
        """Counts available containers objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A number of how many container belongs to the node.
        """
        condition = {"node_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return Container.query.filter_by(**condition).count()

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
        return Container.query.filter_by(**condition).all()

    def as_dict(self):
        return self.resource_fields

    @property
    def resource_fields(self):
        return {}


class DiscoveryNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "discovery",
    }

    # state_node_create = BooleanType(default=False)
    # state_install_consul = BooleanType(default=False)
    # state_complete = BooleanType(default=False)

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
        return self.state_attrs.get("state_node_create")

    @property
    def state_install_consul(self):
        return self.state_attrs.get("state_install_consul")

    @property
    def state_complete(self):
        return self.state_attrs.get("state_complete")


class MsgconNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "msgcon",
    }
    # state_node_create = BooleanType(default=False)
    # state_install_mysql= BooleanType(default=False)
    # state_install_activemq = BooleanType(default=False)
    # state_install_msgcon = BooleanType(default=False)
    # state_pull_images = BooleanType(default=False)
    # state_complete = BooleanType(default=False)

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
        return self.state_attrs.get("state_node_create")

    @property
    def state_install_mysql(self):
        return self.state_attrs.get("state_install_mysql")

    @property
    def state_install_activemq(self):
        return self.state_attrs.get("state_install_activemq")

    @property
    def state_install_msgcon(self):
        return self.state_attrs.get("state_install_msgcon")

    @property
    def state_pull_images(self):
        return self.state_attrs.get("state_pull_images")

    @property
    def state_complete(self):
        return self.state_attrs.get("state_complete")


class MasterNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "master",
    }
    # state_node_create = BooleanType(default=False)
    # state_complete = BooleanType(default=False)
    # state_rng_tools = BooleanType(default=False)
    # state_pull_images = BooleanType(default=False)
    # state_network_create = BooleanType(default=False)

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
        return self.state_attrs.get("state_node_create")

    @property
    def state_complete(self):
        return self.state_attrs.get("state_complete")

    @property
    def state_rng_tools(self):
        return self.state_attrs.get("state_rng_tools")

    @property
    def state_pull_images(self):
        return self.state_attrs.get("state_pull_images")

    @property
    def state_network_create(self):
        return self.state_attrs.get("state_network_create")


class WorkerNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "worker",
    }
    # state_node_create = BooleanType(default=False)
    # state_complete = BooleanType(default=False)
    # state_rng_tools = BooleanType(default=False)
    # state_pull_images = BooleanType(default=False)

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
        return self.state_attrs.get("state_node_create")

    @property
    def state_complete(self):
        return self.state_attrs.get("state_complete")

    @property
    def state_rng_tools(self):
        return self.state_attrs.get("state_rng_tools")

    @property
    def state_pull_images(self):
        return self.state_attrs.get("state_pull_images")
