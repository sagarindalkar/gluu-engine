# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.


class BaseModel(object):
    """Base class for model.

    This class should not be used directly.
    """
    resource_fields = {}

    def as_dict(self):
        fields = tuple(self.resource_fields.keys())
        return {
            k: v for k, v in self.__dict__.items()
            if k in fields
        }


#: A flag to mark state as ``SUCCESS``
STATE_SUCCESS = "SUCCESS"

#: A flag to mark state as ``IN-PROGRESS``
STATE_IN_PROGRESS = "IN_PROGRESS"

#: A flag to mark state as ``FAILED``
STATE_FAILED = "FAILED"

#: A flag to mark state as ``DISABLED``
STATE_DISABLED = "DISABLED"
