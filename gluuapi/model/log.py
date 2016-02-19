# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from .base import BaseModel
from ..database import db


class NodeLog(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "node_name",
        # "setup_log",
        # "teardown_log",
    ])

    def __init__(self):
        self.id = ""
        self.node_name = ""
        self.setup_log = ""
        self.teardown_log = ""

    @staticmethod
    def create_or_get(node):
        try:
            return db.search_from_table(
                "node_logs",
                db.where("node_name") == node.name,
            )[0]
        except IndexError:
            pass

        node_log = NodeLog()
        node_log.id = node.name
        node_log.node_name = node.name
        node_log.setup_log = "{}-setup.log".format(node_log.node_name)
        node_log.teardown_log = "{}-teardown.log".format(node_log.node_name)
        db.persist(node_log, "node_logs")
        return node_log
