# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import time

from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from ..database import db
from ..helper import distribute_cluster_data
from ..model import STATE_DISABLED
from ..model import STATE_SUCCESS
from ..utils import retrieve_signed_license
from ..utils import decode_signed_license
from ..weave import Weave
from ..machine import Machine

# Default interval when running periodic task (set to 1 day)
_DEFAULT_INTERVAL = 60 * 60 * 24


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
        deferred = lc.start(_DEFAULT_INTERVAL, now=True)
        deferred.addErrback(on_error)

    def monitor_license(self):
        """Monitors the license for its expiration status.
        """
        self.logger.info("checking license keys")
        with self.app.app_context():
            license_keys = db.all("license_keys")

            for license_key in license_keys:
                if not license_key.expired:
                    continue

                self.logger.info("found expired license "
                                 "key {}".format(license_key.id))
                self.logger.info("trying to retrieve license update")
                new_license_key = self.update_license_key(license_key)

                worker_nodes = db.search_from_table(
                    "nodes",
                    {"type": "worker"},
                )
                for node in worker_nodes:
                    if new_license_key.expired:
                        # unable to do license_key renewal, hence we're going to
                        # disable oxauth and oxidp containers
                        for type_ in ["oxauth", "oxidp"]:
                            self.disable_containers(node, type_)
                    else:
                        # if we have disabled oxauth and oxidp containers in node
                        # and license key is not expired, try to re-enable
                        # the containers
                        for type_ in ["oxauth", "oxidp"]:
                            self.enable_containers(node, type_)

                if worker_nodes:
                    # delay before distributing the data to worker nodes
                    time.sleep(5)
                    distribute_cluster_data(self.app.config["SHARED_DATABASE_URI"], self.app)

    def update_license_key(self, license_key):
        """Retrieves new license and update the database.

        :param license_key: LicenseKey object.
        :returns: LicenseKey object with updated values.
        """
        resp = retrieve_signed_license(license_key.code)
        if not resp.ok:
            self.logger.warn("unable to retrieve new license; "
                             "reason: {}".format(resp.text))
            return license_key

        self.logger.info("new license has been retrieved")
        try:
            signed_license = resp.json()["license"]
            decoded_license = decode_signed_license(
                signed_license,
                license_key.decrypted_public_key,
                license_key.decrypted_public_password,
                license_key.decrypted_license_password,
            )
        except ValueError as exc:  # pragma: no cover
            self.logger.warn("unable to generate metadata for new license; "
                             "reason={}".format(exc))
            decoded_license["valid"] = False
            decoded_license["metadata"] = {}
        finally:
            license_key.valid = decoded_license["valid"]
            license_key.metadata = decoded_license["metadata"]
            license_key.signed_license = signed_license

        with self.app.app_context():
            db.update(license_key.id, license_key, "license_keys")
        return license_key

    def disable_containers(self, node, type_):
        """Disables containers with certain type.

        Disabled container will be excluded from weave network.

        :param node: Node object.
        :param type_: Type of the container.
        """
        containers = node.get_containers(type_=type_)
        with self.app.app_context():
            for container in containers:
                container.state = STATE_DISABLED
                db.update(container.id, container, "containers")

                self.machine.ssh(node.name, "sudo docker stop {}".format(container.cid))
                self.logger.info("{} container {} has been "
                                 "disabled".format(type_, container.name))

    def enable_containers(self, node, type_):
        """Enables containers with certain type.

        Enabled container will be included into weave network.

        :param node: Node object.
        :param type_: Type of the container.
        """
        weave = Weave(node, self.app, self.logger)

        containers = node.get_containers(type_=type_, state=STATE_DISABLED)
        with self.app.app_context():
            for container in containers:
                container.state = STATE_SUCCESS
                db.update(container.id, container, "containers")

                self.machine.ssh(node.name, "sudo docker restart {}".format(container.cid))
                weave.dns_add(container.cid, container.hostname)
                self.logger.info("{} container {} has been "
                                 "enabled".format(type_, container.id))
