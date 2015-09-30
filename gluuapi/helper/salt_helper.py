# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os

import salt.config
import salt.key
import salt.client
import salt.utils.event


class SaltHelper(object):
    client = salt.client.LocalClient()
    key_store = salt.key.Key(client.opts)
    event = salt.utils.event.get_event(
        "master",
        sock_dir=client.opts["sock_dir"],
        transport=client.opts["transport"],
        opts=client.opts,
    )

    def register_minion(self, key):
        """Registers a minion.

        :param key: Key used by minion; typically a container ID (short format)
        """
        return self.key_store.accept(key, include_rejected=True)

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
        return self.client.cmd(tgt, "cp.recv", [self._load_files([src]), dest])

    def cmd(self, tgt, fun, arg=()):
        return self.client.cmd(tgt, fun, arg)

    def get_fqhostname(self):
        import salt.utils.network
        return salt.utils.network.get_fqhostname()

    def reject_minion(self, key):
        return self.key_store.reject(key, include_accepted=True)
