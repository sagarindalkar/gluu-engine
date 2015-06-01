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
import uuid

from flask_restful_swagger import swagger
from flask_restful.fields import String
from flask_restful.fields import Nested
from flask_restful.fields import Boolean

from gluuapi.database import db
from gluuapi.model.base import BaseModel
from gluuapi.utils import generate_passkey
from gluuapi.utils import timestamp_millis


@swagger.model
class License(BaseModel):
    resource_fields = {
        "id": String,
        "code": String,
        "billing_email": String,
        "valid": Boolean,
        "metadata": Nested,
    }

    def __init__(self, fields=None):
        fields = fields or {}
        self.passkey = generate_passkey()

        self.id = "{}".format(uuid.uuid4())
        self.code = fields.get("code", "")
        self.billing_email = fields.get("billing_email", "")

        # license retrieved from API call to
        # https://license.gluu.org/rest/generate
        self.signed_license = fields.get("signed_license", "")

        self.valid = fields.get("valid", False)
        self.metadata = fields.get("metadata", {})

    @property
    def expired(self):
        if not self.metadata["expiration_date"]:
            return False

        # ``expiration_date`` is time in milliseconds since the EPOCH
        now = timestamp_millis()
        return now > self.metadata["expiration_date"]

    def get_provider_objects(self):
        providers = db.search_from_table("providers", db.where("license_id") == self.id)
        return providers
