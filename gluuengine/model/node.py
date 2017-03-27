# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from sqlalchemy import JSON

from .base import BaseModelMixin
from .base import STATE_SUCCESS
from .container import Container
from ..extensions import db


class Node(BaseModelMixin, db.Model):
    __tablename__ = "nodes"

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


class DiscoveryNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "discovery",
    }

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


@db.event.listens_for(DiscoveryNode, "init")
def receive_init_discovery(target, args, kwargs):
    target.state_attrs = dict.fromkeys([
        "state_node_create",
        "state_install_consul",
        "state_complete",
    ], False)


class MsgconNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "msgcon",
    }

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


@db.event.listens_for(MsgconNode, "init")
def receive_init_msgcon(target, args, kwargs):
    target.state_attrs = dict.fromkeys([
        "state_node_create",
        "state_install_mysql",
        "state_install_activemq",
        "state_install_msgcon",
        "state_pull_images",
        "state_complete",
    ], False)


class MasterNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "master",
    }

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


@db.event.listens_for(MasterNode, "init")
def receive_init_master(target, args, kwargs):
    target.state_attrs = dict.fromkeys([
        "state_node_create",
        "state_complete",
        "state_rng_tools",
        "state_pull_images",
        "state_network_create",
    ], False)


class WorkerNode(Node):
    __mapper_args__ = {
        "polymorphic_identity": "worker",
    }

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


@db.event.listens_for(WorkerNode, "init")
def receive_init_worker(target, args, kwargs):
    target.state_attrs = dict.fromkeys([
        "state_node_create",
        "state_complete",
        "state_rng_tools",
        "state_pull_images",
    ], False)
