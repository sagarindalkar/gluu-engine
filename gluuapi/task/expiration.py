# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import time

from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from ..database import db
from ..helper import WeaveHelper
from ..helper import distribute_cluster_data
from ..model import STATE_DISABLED
from ..model import STATE_SUCCESS
from ..utils import retrieve_signed_license
from ..utils import decode_signed_license

# Default interval when running periodic task (set to 1 day)
_DEFAULT_INTERVAL = 60 * 60 * 24


class LicenseExpirationTask(object):
    def __init__(self, app):
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.app = app

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
        license_keys = db.all("license_keys")

        for license_key in license_keys:
            if not license_key.expired:
                continue

            self.logger.info("found expired license "
                             "key {}".format(license_key.id))

            providers = license_key.get_provider_objects()
            for provider in providers:
                self.logger.info("trying to retrieve new license for "
                                 "provider {}".format(provider.id))

                new_license_key = self.update_license_key(license_key)
                if new_license_key.expired:
                    # unable to do license_key renewal, hence we're going to
                    # disable oxauth and oxidp nodes
                    for type_ in ["oxauth", "oxidp"]:
                        self.disable_nodes(provider, type_)
                else:
                    # if we have disabled oxauth and oxidp nodes in provider
                    # and license key is not expired, try to re-enable
                    # the nodes
                    for type_ in ["oxauth", "oxidp"]:
                        self.enable_nodes(provider, type_)

            if providers:
                # delay before distributing the data to consumers
                time.sleep(5)
                distribute_cluster_data(self.app.config["DATABASE_URI"])

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
        except ValueError:  # pragma: no cover
            self.logger.warn("unable to generate metadata for new license; "
                             "likely caused by incorrect credentials")
            decoded_license["valid"] = False
            decoded_license["metadata"] = {}
        finally:
            license_key.valid = decoded_license["valid"]
            license_key.metadata = decoded_license["metadata"]
            license_key.signed_license = signed_license

        db.update(license_key.id, license_key, "license_keys")
        return license_key

    def disable_nodes(self, provider, type_):
        """Disables nodes with certain type.

        Disabled node will be excluded from weave network.

        :param provider: Provider object.
        :param type_: Type of the node.
        """
        weave = WeaveHelper(provider, self.app, self.logger)

        nodes = provider.get_node_objects(type_=type_)
        for node in nodes:
            node.state = STATE_DISABLED
            db.update(node.id, node, "nodes")

            cidr = "{}/{}".format(node.weave_ip, node.weave_prefixlen)
            weave.detach(cidr, node.id)
            self.logger.info("{} node {} has been "
                             "disabled".format(type_, node.id))

    def enable_nodes(self, provider, type_):
        """Enables nodes with certain type.

        Enabled node will be included into weave network.

        :param provider: Provider object.
        :param type_: Type of the node.
        """
        weave = WeaveHelper(provider, self.app, self.logger)

        nodes = provider.get_node_objects(type_=type_, state=STATE_DISABLED)
        for node in nodes:
            node.state = STATE_SUCCESS
            db.update(node.id, node, "nodes")

            cidr = "{}/{}".format(node.weave_ip, node.weave_prefixlen)
            weave.attach(cidr, node.id)
            weave.dns_add(node.id, node.domain_name)
            self.logger.info("{} node {} has been "
                             "enabled".format(type_, node.id))
