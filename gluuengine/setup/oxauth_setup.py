# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from blinker import signal

from .base import OxSetup


class OxauthSetup(OxSetup):
    def setup(self):
        self.render_ldap_props_template()
        self.write_salt_file()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        return True

    def teardown(self):
        """Teardowns the container.
        """
        complete_sgn = signal("ox_teardown_completed")
        complete_sgn.send(self)

    def after_setup(self):
        """Post-setup callback.
        """
        complete_sgn = signal("ox_setup_completed")
        complete_sgn.send(self)
