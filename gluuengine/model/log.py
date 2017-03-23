# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from ..extensions import db


class ContainerLog(db.Model):
    __tablename__ = "container_logs"

    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    container_name = db.Column(db.Unicode(255))
    state = db.Column(db.Unicode(32))
    setup_log = db.Column(db.Unicode(255))
    teardown_log = db.Column(db.Unicode(255))

    @property
    def resource_fields(self):
        return {
            "id": self.id,
            "container_name": self.container_name,
            "state": self.state,
        }

    @staticmethod
    def create_or_get(container):
        container_log = ContainerLog.query.filter_by(
            container_name=container.name
        ).first()

        if container_log:
            return container_log

        container_log = ContainerLog()
        container_log.container_name = container.name
        container_log.setup_log = "{}-setup.log".format(
            container_log.container_name
        )
        container_log.teardown_log = "{}-teardown.log".format(
            container_log.container_name
        )
        db.session.add(container_log)
        db.session.commit()
        return container_log

    def as_dict(self):
        return self.resource_fields
