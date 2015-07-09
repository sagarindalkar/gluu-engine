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
from gluuapi.utils import timestamp_millis
from gluuapi.helper import SaltHelper
from gluuapi.model import License
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
        self.logger.info("checking expired licenses")
        field = db.where("metadata").has("expiration_date")
        condition = (field < timestamp_millis())
        licenses = db.search_from_table("licenses", condition)

        for license in licenses:
            if not license.expired:  # pragma: no cover
                continue

            self.logger.info("found expired license {}".format(license.id))

            providers = license.get_provider_objects()
            for provider in providers:
                # if we have providers affected by this license,
                # try to retrieve new license and update related provider
                # to use the new license
                self.logger.info("trying to retrieve new license for "
                                 "provider {}".format(provider.id))

                try:
                    code = license.get_license_key().code
                except AttributeError:
                    code = ""

                new_license = self.get_new_license(
                    code, license.license_key_id,
                )
                if new_license and not new_license.expired:
                    # only update provider when new license has correct metadata
                    provider.license_id = new_license.id
                    db.update(provider.id, provider, "providers")
                    self.logger.info("provider {} has been "
                                     "updated".format(provider.id))
                    continue

                # unable to do license renewal, hence we're going to
                # disable oxAuth nodes
                self.disable_oxauth_nodes(provider)

    def get_new_license(self, code, license_key_id):
        resp = retrieve_signed_license(code)
        if not resp.ok:
            self.logger.warn("unable to retrieve new license; "
                             "reason: {}".format(resp.text))
            return

        # new license is retrieved
        self.logger.info("new license has been retrieved")
        params = {
            "signed_license": resp.json()["license"],
            "license_key_id": license_key_id,
            "code": code,
        }

        license = License(params)
        credential = db.get(license.license_key_id, "license_keys")

        try:
            decoded_license = decode_signed_license(
                license.signed_license,
                credential.decrypted_public_key,
                credential.decrypted_public_password,
                credential.decrypted_license_password,
            )
        except ValueError:  # pragma: no cover
            self.logger.warn("unable to generate metadata for new license; "
                             "likely caused by incorrect credentials")
        else:
            license.valid = decoded_license["valid"]
            license.metadata = decoded_license["metadata"]

        # saves this new license
        db.persist(license, "licenses")
        return license

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
