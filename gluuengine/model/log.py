# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from schematics.types import StringType

from ._schema import CONTAINER_LOG_SCHEMA
from .base import BaseModel
from ..database import db


class ContainerLog(BaseModel):
    @property
    def _schema(self):
        return CONTAINER_LOG_SCHEMA

    id = StringType(default=lambda: str(uuid.uuid4()))
    container_name = StringType()
    setup_log = StringType()
    teardown_log = StringType()
    state = StringType()
    _pyobject = StringType()

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "container_name": self.container_name,
            "state": self.state,
        }

    @staticmethod
    def create_or_get(container):
        try:
            return db.search_from_table(
                "container_logs",
                {"container_name": container.name},
            )[0]
        except IndexError:
            pass

        container_log = ContainerLog()
        container_log.container_name = container.name
        container_log.setup_log = "{}-setup.log".format(container_log.container_name)  # noqa
        container_log.teardown_log = "{}-teardown.log".format(container_log.container_name)  # noqa
        db.persist(container_log, "container_logs")
        return container_log
