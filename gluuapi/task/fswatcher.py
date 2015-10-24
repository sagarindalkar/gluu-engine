# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging

from crochet import run_in_reactor
from twisted.internet import inotify
from twisted.python import filepath

from ..database import db
from ..helper import SaltHelper


class SamlWatcherTask(object):
    def __init__(self):
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.watcher = inotify.INotify()
        self.salt = SaltHelper()

        # path to a directory where all filesystem
        # should be watched for
        self.path = "/etc/gluu/saml"

        # list of file extensions should be watched for
        self.allowed_extensions = (
            ".xml", ".config", ".xsd", ".dtd",
        )

        # cluster object may not be created yet
        # when the task is launched
        try:
            self.cluster = db.all("clusters")[0]
        except IndexError:
            self.cluster = None

    @run_in_reactor
    def perform_job(self):
        self.logger.info("Listening for filesystem events "
                         "in {}".format(self.path))

        self.watcher.startReading()
        fp = filepath.FilePath(self.path)

        try:
            # ensure directory exists
            fp.makedirs()
        except OSError:
            # likely the directory is exist
            pass

        self.watcher.watch(
            filepath.FilePath(self.path),
            autoAdd=True,
            callbacks=[self.process_event],
            recursive=True,
        )

    def process_event(self, watch, path, mask):
        """Intercepts filesystem event.
        """
        callbacks = {
            inotify.IN_MODIFY: self.on_modified,
            inotify.IN_CREATE: self.on_created,
        }
        callback = callbacks.get(mask, None)
        if callback is not None:
            callback(path.realpath())

    def on_modified(self, fp):
        """A callback when _modify_ event occurs.
        """
        if fp.splitext()[-1] not in self.allowed_extensions:
            return
        self.distribute_file(fp.path)

    def on_created(self, fp):
        """A callback when _create_ event occurs.
        """
        if fp.splitext()[-1] not in self.allowed_extensions:
            return
        self.distribute_file(fp.path)

    def distribute_file(self, src):
        """Copy the files from mapped volume to all saml nodes.
        """
        if not self.cluster:
            self.logger.warn("Unable to find existing cluster; "
                             "skipping {} distribution".format(src))
            return

        # oxTrust will generate required files for Shib configuration
        # under ``/opt/idp`` inside the container; this directory
        # is mapped as ``/etc/gluu/saml`` inside the host
        #
        # for example, given a file ``/opt/idp/conf/attribute-resolver.xml``
        # created inside the container, it will be mapped to
        # ``/etc/gluu/saml/conf/attribute-resolver.xml`` inside the host
        #
        # we need to distribute this file to
        # ``/opt/idp/conf/attribute-resolver.xml`` inside the saml node
        # (gluushib)
        dest = src.replace("/etc/gluu/saml", "/opt/idp")
        saml_nodes = self.cluster.get_saml_objects()

        for saml in saml_nodes:
            self.logger.info("Found existing saml node "
                             "with ID {}".format(saml.id))
            self.logger.info("copying {} to {}:{}".format(
                src, saml.name, dest,
            ))
            self.salt.copy_file(saml.id, src, dest)
