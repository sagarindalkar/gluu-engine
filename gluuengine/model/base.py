# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from schematics.models import Model


class BaseModel(Model):
    resource_fields = tuple([])

    def __init__(self, raw_data=None, deserialize_mapping=None, strict=True):
        super(BaseModel, self).__init__(
            raw_data=raw_data,
            deserialize_mapping=deserialize_mapping,
            strict=False,
        )

    def expose_public_fields(self):
        return {
            k: v for k, v in self.to_primitive().iteritems()
            if k in self.resource_fields
        }

    def as_dict(self):
        return self.expose_public_fields()


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
