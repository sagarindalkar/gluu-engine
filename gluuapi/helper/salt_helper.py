# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import os
import time

import salt.config
import salt.key
import salt.client
import salt.utils.event

from ..errors import SaltEventError

SALT_EVENT_TIMEOUT = 2 * 60


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
        """Copies file to minion.
        """
        ret = self.cmd(tgt, "cp.recv", [self._load_files([src]), dest])
        time.sleep(1)

        max_retry = 5
        retry_attempt = 0

        while retry_attempt < max_retry:
            # response from minion will be ``{'minion_id': True}``
            # if file exists, otherwise ``{'minion_id': ''}`` if file
            # not exist
            resp = self.cmd(tgt, "file.file_exists", [dest])
            if resp.get(tgt):
                break

            # re-copy the file, but this time we will wait for 5 seconds
            # before doing subsequent checks
            ret = self.cmd(tgt, "cp.recv", [self._load_files([src]), dest])
            time.sleep(5)

            # mark as N-time retry attempt
            retry_attempt += 1
        return ret

    def cmd(self, tgt, fun, arg=()):
        """Runs synchronous command in minion.
        """
        return self.client.cmd(tgt, fun, arg)

    def reject_minion(self, key):
        """Rejects minion from keystore.
        """
        return self.key_store.reject(key, include_accepted=True)

    def cmd_async(self, tgt, fun, arg=()):
        """Runs asynchronous command in minion.
        """
        return self.client.cmd_async(tgt, fun, arg)

    @classmethod
    def subscribe_event(cls, jid, key, wait=SALT_EVENT_TIMEOUT,
                        skip_retcodes=None, silent=False, err_msg=""):
        """Subscribes to salt event and respond necessarily.
        """
        skip_retcodes = skip_retcodes or []
        skip_retcodes = set(skip_retcodes + [0])
        err_msg = err_msg or "failed to execute command"

        tag = "salt/job/{}/ret/{}".format(jid, key)
        ret = cls.event.get_event(wait=wait, tag=tag, full=True) or {}

        if not silent:
            if not ret:
                cmd_err = "unable to get response from minion {} " \
                          "for jid {} within {} seconds".format(key, jid, wait)
                raise SaltEventError(err_msg, cmd_err)

            if ret["data"]["retcode"] not in skip_retcodes:
                raise SaltEventError(err_msg, ret["data"]["return"],
                                     exit_code=ret["data"]["retcode"])
        return ret


def prepare_minion(key, connect_delay=10, exec_delay=15, logger=None):
    """Waits for minion to connect before doing any remote execution.

    :param key: Minion ID.
    :param connect_delay: Time to wait before start connecting to minion.
    :param exec_delay: Time to wait before start executing remote command.
    :param logger: Instance of logger object.
    """
    # wait for 10 seconds to make sure minion connected
    # and sent its key to master
    # TODO: there must be a way around this
    if logger:
        logger.info("Waiting for minion to connect; sleeping for "
                    "{} seconds".format(connect_delay))
    time.sleep(connect_delay)

    # register the container as minion
    salt = SaltHelper()
    salt.register_minion(key)

    # delay the remote execution
    # see https://github.com/saltstack/salt/issues/13561
    # TODO: there must be a way around this
    if logger:
        logger.info("Preparing remote execution; sleeping for "
                    "{} seconds".format(exec_delay))
    time.sleep(exec_delay)
