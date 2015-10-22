# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging

from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from ..database import db
from ..helper import WeaveHelper
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
    def start(self, interval=_DEFAULT_INTERVAL):
        # callback to handle error
        def on_error(failure):
            self.logger.error(failure.getTraceback())

        lc = LoopingCall(self.perform_job)
        deferred = lc.start(interval, now=True)
        deferred.addErrback(on_error)

    def perform_job(self):
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
                    # disable oxAuth nodes
                    self.disable_oxauth_nodes(provider)
                else:
                    # if we have disabled oxAuth nodes in provider
                    # and license key is not expired, try to re-enable
                    # the nodes
                    self.enable_oxauth_nodes(provider)

    def update_license_key(self, license_key):
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

    def disable_oxauth_nodes(self, provider):
        weave = WeaveHelper(provider, self.app, self.logger)

        for node in provider.get_node_objects(type_="oxauth"):
            node.state = STATE_DISABLED
            db.update(node.id, node, "nodes")

            cidr = "{}/{}".format(node.weave_ip, node.weave_prefixlen)
            weave.detach(cidr, node.id)
            self.logger.info("{} node {} has been disabled".format("oxauth", node.id))

    def enable_oxauth_nodes(self, provider):
        weave = WeaveHelper(provider, self.app, self.logger)

        for node in provider.get_node_objects(type_="oxauth", state=STATE_DISABLED):
            node.state = STATE_SUCCESS
            db.update(node.id, node, "nodes")

            cidr = "{}/{}".format(node.weave_ip, node.weave_prefixlen)
            weave.attach(cidr, node.id)
            self.logger.info("{} node {} has been enabled".format("oxauth", node.id))
