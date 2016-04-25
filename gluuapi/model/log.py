# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel
from ..database import db


class ContainerLog(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "container_name",
        "setup_log_url",
        "teardown_log_url",
        "state",
    ])

    def __init__(self):
        self.id = ""
        self.container_name = ""
        self.setup_log = ""
        self.setup_log_url = ""
        self.teardown_log = ""
        self.teardown_log_url = ""
        self.state = ""

    @staticmethod
    def create_or_get(container):
        try:
            return db.search_from_table(
                "container_logs",
                db.where("container_name") == container.name,
            )[0]
        except IndexError:
            pass

        container_log = ContainerLog()
        container_log.id = container.name
        container_log.container_name = container.name
        container_log.setup_log = "{}-setup.log".format(container_log.container_name)
        container_log.teardown_log = "{}-teardown.log".format(container_log.node_name)
        db.persist(container_log, "node_logs")
        return container_log
