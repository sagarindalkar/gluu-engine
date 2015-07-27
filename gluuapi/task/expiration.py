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
import logging

from crochet import run_in_reactor
from twisted.internet.task import LoopingCall

from gluuapi.database import db
from gluuapi.helper import SaltHelper
from gluuapi.model import STATE_DISABLED
from gluuapi.utils import retrieve_signed_license
from gluuapi.utils import decode_signed_license

# Default interval when running periodic task (set to 1 day)
_DEFAULT_INTERVAL = 60 * 60 * 24


class LicenseExpirationTask(object):
    def __init__(self):
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.salt = SaltHelper()

    @run_in_reactor
    def start(self, interval=_DEFAULT_INTERVAL):
        # callback to handle error
        def on_error(failure):
            self.logger.error(failure.getTraceback())

        lc = LoopingCall(self.perform_job)
        deferred = lc.start(interval, now=True)
        deferred.addErrback(on_error)

    def perform_job(self):
        self.logger.info("checking expired license keys")
        license_keys = db.all("license_keys")

        for license_key in license_keys:
            if not license_key.expired:  # pragma: no cover
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

    def update_license_key(self, license_key):
        resp = retrieve_signed_license(license_key.code)
        if not resp.ok:
            self.logger.warn("unable to retrieve new license; "
                             "reason: {}".format(resp.text))
            return license_key

        self.logger.info("new license has been retrieved")
        try:
            decoded_license = decode_signed_license(
                resp.json()["license"],
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

        db.update(license_key.id, license_key, "license_keys")
        return license_key

    def disable_oxauth_nodes(self, provider):
        for node in provider.get_node_objects(type_="oxauth"):
            self.logger.info("disabling oxAuth node {}".format(node.id))
            detach_cmd = "weave detach {}/{} {}".format(
                node.weave_ip,
                node.weave_prefixlen,
                node.id,
            )
            node.state = STATE_DISABLED
            db.update(node.id, node, "nodes")
            self.salt.cmd(provider.hostname, "cmd.run", [detach_cmd])
            self.logger.info("oxAuth node {} has been "
                             "disabled".format(node.id))
