# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid
from datetime import datetime

from ..extensions import db

#: A flag to mark state as ``SUCCESS``
STATE_SUCCESS = "SUCCESS"

#: A flag to mark state as ``IN-PROGRESS``
STATE_IN_PROGRESS = "IN_PROGRESS"

#: A flag to mark state as ``FAILED``
STATE_FAILED = "FAILED"

#: A flag to mark state as ``DISABLED``
STATE_DISABLED = "DISABLED"

STATE_SETUP_IN_PROGRESS = "SETUP_IN_PROGRESS"
STATE_SETUP_FINISHED = "SETUP_FINISHED"
STATE_TEARDOWN_IN_PROGRESS = "TEARDOWN_IN_PROGRESS"
STATE_TEARDOWN_FINISHED = "TEARDOWN_FINISHED"


class BaseModelMixin(object):
    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime(True), default=datetime.utcnow)

    @property
    def resource_fields(self):
        return {}

    def as_dict(self):
        return self.resource_fields
