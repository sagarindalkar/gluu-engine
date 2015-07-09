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
from urllib import quote_plus

from marshmallow import post_load
from marshmallow import validates
from marshmallow import ValidationError

from gluuapi.database import db
from gluuapi.extensions import ma


class LicenseReq(ma.Schema):
    license_key_id = ma.Str(required=True)

    @validates("license_key_id")
    def validate_credential_id(self, value):
        license_key = db.get(value, "license_keys")
        self.context["license_key"] = license_key

        if not license_key:
            raise ValidationError("invalid license key")

    @post_load
    def finalize_data(self, data):
        out = {"params": data}
        out.update({"context": self.context})
        return out


class LicenseKeyReq(ma.Schema):
    name = ma.Str(required=True)
    code = ma.Str(required=True)
    public_key = ma.Str(required=True)
    public_password = ma.Str(required=True)
    license_password = ma.Str(required=True)

    @post_load
    def urlsafe_public_key(self, data):
        # public key from license server is not URL-safe
        # client like ``curl`` will interpret ``+`` as whitespace
        # hence we're converting whitespace to ``+``
        data["public_key"] = quote_plus(data.get("public_key", ""), safe="/+=")
        return data
