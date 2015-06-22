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
import re

from marshmallow import validates
from marshmallow import ValidationError

from gluuapi.extensions import ma
from gluuapi.database import db

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')


class ProviderReq(ma.Schema):
    hostname = ma.Str(required=True)
    docker_base_url = ma.Str(required=True)
    license_id = ma.Str(default="", missing="")

    @validates("hostname")
    def validate_hostname(self, value):
        # some provider like AWS uses dotted hostname,
        # e.g. ip-172-31-24-54.ec2.internal
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid:
            raise ValidationError("invalid hostname")

    @validates("license_id")
    def validate_license_id(self, value):
        if value:
            licensed_count = db.count_from_table(
                "providers",
                db.where("license_id") == value,
            )
            if licensed_count:
                raise ValidationError("cannot reuse license")

            license = db.get(value, "licenses")
            if not license:
                raise ValidationError("invalid license ID")
            if license.expired:
                raise ValidationError("expired license")


class EditProviderReq(ProviderReq):
    @validates("license_id")
    def validate_license_id(self, value):
        provider = self.context["provider"]
        if provider.type == "consumer":
            if not value:
                raise ValidationError("the value is required for consumer")

            # counts license used by another provider (if any)
            licensed_count = db.count_from_table(
                "providers",
                ((db.where("license_id") == value)
                 & (db.where("id") != provider.id)),
            )

            # license cannot be reuse
            if licensed_count:
                raise ValidationError("cannot reuse license")

            license = db.get(value, "licenses")
            if not license:
                raise ValidationError("invalid license ID")
            if license.expired:
                raise ValidationError("expired license")
