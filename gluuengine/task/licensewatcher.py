# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import time

from crochet import run_in_reactor
from requests.exceptions import ConnectionError
from twisted.internet.task import LoopingCall

from ..extensions import db
from ..model import STATE_DISABLED
from ..model import STATE_SUCCESS
from ..model import LicenseKey
from ..machine import Machine
from ..utils import populate_license
from ..utils import retrieve_current_date

# Default interval when running periodic task (set to 1 day)
TASK_INTERVAL = 60 * 60 * 24

# Default interval (in milliseconds) to check neccessary update
UPDATE_INTERVAL_MILLIS = 60 * 60 * 24 * 1000

# Retry interval for updating license (if previous attempt is failed)
RETRY_INTERVAL = 60 * 60 * 3

# Maximum retries for updating license
RETRY_LIMIT = 3


class LicenseWatcherTask(object):
    def __init__(self, app):
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.app = app
        self.machine = Machine()

    @run_in_reactor
    def perform_job(self):
        """An entrypoint of this task class.
        """
        # callback to handle error
        def on_error(failure):
            self.logger.error(failure.getTraceback())

        lc = LoopingCall(self.monitor_license)
        deferred = lc.start(TASK_INTERVAL, now=True)
        deferred.addErrback(on_error)

    def monitor_license(self):
        license_key = self.get_license_key()
        err = ""

        self.logger.info("checking license key")

        if not license_key:
            self.logger.info("license key is currently unavailable")
            return

        if not license_key.auto_update:
            self.logger.info("auto-update feature for license is disabled")
            return

        self.logger.info("auto-updating license")

        try:
            # get current datetime from license server
            current_date = retrieve_current_date()
        except ConnectionError:
            self.logger.warn("unable to get current date from license server")
            return

        # if license has been already updated within 24 hours,
        # no need to re-populate the license
        if (current_date - license_key.updated_at) < UPDATE_INTERVAL_MILLIS:
            self.logger.info("license key is up-to-date")
            return

        # do retries (max. 3 times)
        retry_attempt = 0

        while True:
            # re-populate the license; this will also send MAC address
            self.logger.info("downloading signed license")
            license_key, err = populate_license(license_key)

            if err:
                self.logger.warn(err)

                if retry_attempt == RETRY_LIMIT:
                    self.logger.warn("failed to update license after "
                                     "few retries")
                    break

                self.logger.info(
                    "auto-retry in {} seconds".format(RETRY_INTERVAL)
                )
                time.sleep(RETRY_INTERVAL)
                retry_attempt += 1
            else:
                # mark the latest update time
                license_key.updated_at = retrieve_current_date()
                with self.app.app_context():
                    db.session.add(license_key)
                    db.session.commit()
                self.logger.info("license key has been updated")
                break

        with self.app.app_context():
            worker_nodes = license_key.get_workers()

        # cache the expiration state
        license_expired = license_key.expired

        for node in worker_nodes:
            if license_expired:
                # disable specific containers
                self.disable_containers(node, "oxauth")
            else:
                # if we have specific containers being disabled in node,
                # try to re-enable the containers
                self.enable_containers(node, "oxauth")

    def get_license_key(self):
        with self.app.app_context():
            return LicenseKey.query.first()

    def disable_containers(self, node, type_):
        """Disables containers having specific type.

        Disabled container will be stopped and excluded from cluster's network.

        :param node: Node object.
        :param type_: Type of the container.
        """
        with self.app.app_context():
            containers = node.get_containers(type_=type_)

            for container in containers:
                container.state = STATE_DISABLED
                db.session.add(container)
                db.session.commit()

                self.machine.ssh(
                    node.name, "sudo docker stop {}".format(container.cid),
                )
                self.logger.info("{} container {} has been "
                                 "disabled".format(type_, container.name))

    def enable_containers(self, node, type_):
        """Enables containers having specific type.

        Enabled container will be restarted and included into cluster's network.

        :param node: Node object.
        :param type_: Type of the container.
        """
        with self.app.app_context():
            containers = node.get_containers(type_=type_, state=STATE_DISABLED)

            for container in containers:
                container.state = STATE_SUCCESS
                db.session.add(container)
                db.session.commit()

                self.machine.ssh(
                    node.name, "sudo docker restart {}".format(container.cid),
                )
                self.logger.info("{} container {} has been "
                                 "enabled".format(type_, container.id))
