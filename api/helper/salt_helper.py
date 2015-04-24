# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import codecs
import os


class SaltHelper(object):
    def __init__(self):
        # salt supresses the flask logger, hence we import salt inside
        # this function as a workaround
        import salt.config
        import salt.key
        import salt.client

        opts = salt.config.client_config("/etc/salt/master")
        self.key_store = salt.key.Key(opts)
        self.client = salt.client.get_local_client(opts["conf_file"])

    def register_minion(self, key):
        """Registers a minion.

        :param key: Key used by minion; typically a container ID (short format)
        """
        return self.key_store.accept(key)

    def unregister_minion(self, key):
        """Unregisters a minion.

        :param key: Key used by minion; typically a container ID (short format)
        """
        return self.key_store.delete_key(key)

    def is_minion_registered(self, key):
        keys = self.key_store.list_keys()
        return key in keys["minions"]

    def _file_dict(self, fn_):
        """Take a path and return the contents of the file as a string
        """
        with codecs.open(fn_, "r", encoding="utf-8") as fp:
            data = fp.read()
        return {fn_: data}

    def _load_files(self, src):
        """Parse the files indicated in ``src`` and load them into
        a python object for transport.
        """
        files = {}
        for fn_ in src:
            if os.path.isfile(fn_):
                files.update(self._file_dict(fn_))
            elif os.path.isdir(fn_):
                raise ValueError("{} is a directory, only files "
                                 "are supported.".format(fn_))
        return files

    def copy_file(self, tgt, src, dest):
        self.client.cmd(tgt, "cp.recv", [self._load_files([src]), dest])

    def cmd(self, tgt, fun, arg=()):
        self.client.cmd(tgt, fun, arg)
