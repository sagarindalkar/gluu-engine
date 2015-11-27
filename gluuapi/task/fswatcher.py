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


class OxidpWatcherTask(object):
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.watcher = inotify.INotify()
        self.salt = SaltHelper()

        # path to a directory where all filesystem
        # should be watched for
        self.path = self.app.config["OXIDP_VOLUMES_DIR"]

        # list of file extensions should be watched for
        self.allowed_extensions = (
            ".xml", ".config", ".xsd", ".dtd",
        )

        # cluster object may not be created yet
        # when the task is launched
        self._cluster = None

    @run_in_reactor
    def perform_job(self):
        """An entrypoint of this task class.
        """
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

        The following filesystem events are watched:

        1. file modification
        2. file creation
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
        """Copy the files from mapped volume to all oxidp nodes.
        """
        if not self.cluster:
            self.logger.warn("Unable to find existing cluster; "
                             "skipping {} distribution".format(src))
            return

        # oxTrust will generate required files for Shib configuration
        # under ``/opt/idp`` inside the container; this directory
        # is mapped as ``/var/lib/gluu-cluster/volumes/oxidp`` inside the host
        #
        # for example, given a file ``/opt/idp/conf/attribute-resolver.xml``
        # created inside the container, it will be mapped to
        # ``/var/lib/gluu-cluster/volumes/oxidp/conf/attribute-resolver.xml`` inside the host
        #
        # we need to distribute this file to
        # ``/opt/idp/conf/attribute-resolver.xml`` inside the oxidp node
        dest = src.replace(self.path, "/opt/idp")
        oxidp_nodes = self.cluster.get_oxidp_objects()

        for node in oxidp_nodes:
            self.logger.info("Found existing oxidp node "
                             "with ID {}".format(node.id))
            self.logger.info("copying {} to {}:{}".format(
                src, node.name, dest,
            ))
            self.salt.copy_file(node.id, src, dest)

    @property
    def cluster(self):
        """Gets a Cluster object.
        """
        if self._cluster is None:
            try:
                self._cluster = db.all("clusters")[0]
            except IndexError:
                self._cluster = None
        return self._cluster
