# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging

from crochet import run_in_reactor
from twisted.internet import inotify
from twisted.python import filepath

from ..database import db
from ..machine import Machine
from ..dockerclient import Docker


class BaseWatcherTask(object):
    #: List of file extensions should be watched for
    allowed_extensions = tuple()

    container_type = ""

    @property
    def src_dir(self):
        """Path to a directory where all filesystem events should be
        watched for.
        """

    @property
    def dest_dir(self):
        """Path to a directory where all filesystem events should be
        copied to.
        """

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

    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.logger = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__),
        )
        self.watcher = inotify.INotify()
        self.machine = Machine()

        # cluster object may not be created yet
        # when the task is launched
        self._cluster = None

    @run_in_reactor
    def perform_job(self):
        """An entrypoint of this task class.
        """
        self.logger.info("Listening for filesystem events "
                         "in {}".format(self.src_dir))

        self.watcher.startReading()
        fp = filepath.FilePath(self.src_dir)

        try:
            # ensure directory exists
            fp.makedirs()
        except OSError:
            # likely the directory is exist
            pass

        self.watcher.watch(
            filepath.FilePath(self.src_dir),
            autoAdd=True,
            callbacks=[self.process_event],
            recursive=True,
        )

    def process_event(self, watch, path, mask):
        """Intercepts filesystem event.

        The following filesystem events are watched:

        1. file modification
        2. file creation
        3. moved file
        4. metadata modification (e.g. ``touch`` command)
        """

        self.logger.info("got {} event for {}".format(
            inotify.humanReadableMask(mask),
            path.realpath().path,
        ))

        callbacks = {
            inotify.IN_MODIFY: self.copy_file,
            inotify.IN_CREATE: self.copy_file,
            inotify.IN_MOVED_TO: self.copy_file,
            inotify.IN_ATTRIB: self.copy_file,
            inotify.IN_CLOSE_WRITE | inotify.IN_CREATE: self.copy_file,
        }
        callback = callbacks.get(mask, None)
        if callback is not None:
            callback(path.realpath())

    def copy_file(self, fp):
        """Copy the files from mapped volume to all related nodes.

        :param fp: FilePath instance.
        """
        # string of absolute path to file
        src = fp.realpath().path
        dest = src.replace(self.src_dir, self.dest_dir)

        if not self.cluster:
            self.logger.warn("Unable to find existing cluster; "
                             "skipping {} distribution".format(src))
            return

        if (self.allowed_extensions and
                fp.splitext()[-1] not in self.allowed_extensions):
            self.logger.warn(
                "File extension {} is not allowed; skipping {} "
                "distribution".format(fp.splitext()[-1], src)
            )
            return

        # get swarm master node
        try:
            master_node = db.search_from_table(
                "node", db.where("type") == "master",
            )[0]
        except IndexError:
            master_node = None

        if not master_node:
            self.logger.warn("unable to find master node")
            return

        dk = Docker(
            self.machine.config(master_node.name),
            self.machine.swarm_config(master_node.name),
        )

        for container in self.get_containers():
            self.logger.info(
                "Found existing {} container with ID {}".format(
                    self.container_type, container.cid))

            self.logger.info("copying {} to {}:{}".format(
                src, container.name, dest,
            ))

            # # copy the file to container
            dk.copy_to_container(container.cid, src, dest)

    def get_containers(self):
        return self.cluster.get_containers(type_=self.container_type)


class OxidpWatcherTask(BaseWatcherTask):
    container_type = "oxidp"
    allowed_extensions = (
        ".xml",
        ".config",
        ".xsd",
        ".dtd",
    )
    dest_dir = "/opt/idp"

    @property
    def src_dir(self):
        return self.app.config["OXIDP_OVERRIDE_DIR"]


class OxauthWatcherTask(BaseWatcherTask):  # pragma: no cover
    container_type = "oxauth"
    dest_dir = "/var/gluu/webapps/oxauth"

    @property
    def src_dir(self):
        return self.app.config["OXAUTH_OVERRIDE_DIR"]


class OxtrustWatcherTask(BaseWatcherTask):  # pragma: no cover
    container_type = "oxtrust"
    dest_dir = "/var/gluu/webapps/oxtrust"

    @property
    def src_dir(self):
        return self.app.config["OXTRUST_OVERRIDE_DIR"]
