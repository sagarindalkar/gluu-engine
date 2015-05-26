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

from gluuapi.model.base import BaseModel
# from gluuapi.utils import encrypt_text
# from gluuapi.utils import decrypt_text
# from gluuapi.utils import get_random_chars
from gluuapi.utils import generate_passkey


@swagger.model
class License(BaseModel):
    resource_fields = {
        "id": String,
        "code": String,
        "name": String,
    }

    def __init__(self, fields=None):
        fields = fields or {}
        self.passkey = generate_passkey()

        self.id = "{}".format(uuid.uuid4())
        self.name = fields.get("name", "")
        self.code = fields.get("code", "")

        # public_key = fields.get("public_key", get_random_chars())
        # self.public_key = encrypt_text(public_key, self.passkey)

        # public_password = fields.get("public_password", get_random_chars())
        # self.public_password = encrypt_text(public_password, self.passkey)

        # license_password = fields.get("license_password", get_random_chars())
        # self.license_password = encrypt_text(license_password, self.passkey)

        # license retrieved from API call to
        # https://license.gluu.org/rest/generate
        self.signed_license = fields.get("signed_license", "")
        # self.signed_license = encrypt_text(signed_license, self.passkey)

    # @property
    # def decrypted_public_key(self):
    #     return decrypt_text(self.public_key, self.passkey)

    # @property
    # def decrypted_public_password(self):
    #     return decrypt_text(self.public_password, self.passkey)

    # @property
    # def decrypted_license_password(self):
    #     return decrypt_text(self.license_password, self.passkey)

    # @property
    # def decrypted_signed_license(self):
    #     return decrypt_text(self.signed_license, self.passkey)
