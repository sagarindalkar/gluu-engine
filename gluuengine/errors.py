# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.


class DockerExecError(Exception):
    def __init__(self, msg, cmd_err="", exit_code=None):
        self.msg = msg
        self.cmd_err = cmd_err
        self.exit_code = exit_code

    def __str__(self):
        return repr("{}: {}".format(self.msg, self.cmd_err))
