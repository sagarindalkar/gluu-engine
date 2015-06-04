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
from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from gluuapi.database import db
from gluuapi.utils import timestamp_millis
from gluuapi.helper import SaltHelper

import logging


# Default interval when running periodic task (set to 1 day)
_DEFAULT_INTERVAL = 60 * 60 * 24


class LicenseExpirationTask(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.salt = SaltHelper()

    @run_in_reactor
    def start(self, interval=_DEFAULT_INTERVAL):
        # callback to handle error
        def on_error(failure):
            self.logger.error(failure.getTraceback())

        lc = LoopingCall(self._get_expired_licenses)
        deferred = lc.start(interval, now=True)
        deferred.addErrback(on_error)

    def _get_expired_licenses(self):
        self.logger.info("checking expired licenses")
        field = db.where("metadata").has("expiration_date")
        condition = (field < timestamp_millis())
        licenses = db.search_from_table("licenses", condition)

        for license in licenses:
            if not license.expired:
                continue
            self.logger.info("found expired license {}".format(license.id))
            self._get_providers(license)

    def _get_providers(self, license):
        for provider in license.get_provider_objects():
            self.logger.info(
                "found provider {} with expired license {}".format(
                    provider.id, license.id)
            )
            self._get_nodes(provider)

    def _get_nodes(self, provider):
        nodes = provider.get_node_objects(type_="oxauth")
        for node in nodes:
            self.logger.info("disabling oxAuth node {}".format(node.id))
            detach_cmd = "weave detach {}/{} {}".format(
                node.weave_ip,
                node.weave_prefixlen,
                node.id,
            )
            self.salt.cmd(provider.hostname, "cmd.run", [detach_cmd])
            self.logger.info("oxAuth node {} has been disabled".format(node.id))
