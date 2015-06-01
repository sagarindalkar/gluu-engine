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
# from flask_mail import Message

# from gluuapi.extensions import mail
# # from gluuapi.database import db
# from gluuapi.utils import timestamp_millis_to_datetime


# def two_months_retention(license):
#     print("checking license about to expire within 60 days")


# # def one_week_retention(license_id):
# def one_week_retention(license):
#     # license = db.get(license_id, "licenses")
#     # if license:
#     dt = timestamp_millis_to_datetime(license.metadata["expiration_date"])
#     msg = Message(
#         subject="License expiration reminder",
#         body=" ".join([
#             "Your license (ID: {}) is about to expire".format(license.id),
#             "in {}".format(dt.strftime("%Y-%m-%d %H:%M:%I (UTC)")),
#         ]),
#         recipients=[license.billing_email],
#     )
#     print(msg)
#     mail.send(msg)
from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from gluuapi.database import db
from gluuapi.helper import SaltHelper
from gluuapi.utils import timestamp_millis

import logging
logging.getLogger("twisted") \
       .addHandler(logging.StreamHandler())


class LicenseExpirationTask(object):
    def __init__(self):
        self._logger = None
        self.salt = SaltHelper()

    @property
    def logger(self):
        if not self._logger:
            fmt = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s  - %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(fmt)

            self._logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
        return self._logger

    @run_in_reactor
    def start(self, interval=10):
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
