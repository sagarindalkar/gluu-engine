# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from blinker import signal

from .base import BaseSetup


class OxelevenSetup(BaseSetup):
    
    def setup(self):
        return True

    def after_setup(self):
        """Post-setup callback.
        """
        return True

    def teardown(self):
        """Teardowns the container.
        """
        return True
