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
from flask import url_for
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.reqparser import provider_req
from gluuapi.model import Provider
from gluuapi.helper import SaltHelper
from gluuapi.utils import decode_signed_license


def format_provider_resp(provider):
    item = provider.as_dict()
    item["type"] = provider.type
    return item


class ProviderResource(Resource):
    @swagger.operation(
        notes="Gives provider info/state",
        nickname="getprovider",
        responseMessages=[
            {
              "code": 200,
              "message": "Provider information",
            },
            {
                "code": 404,
                "message": "Provider not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
    )
    def get(self, provider_id):
        obj = db.get(provider_id, "providers")
        if not obj:
            return {"code": 404, "message": "Provider not found"}, 404
        return format_provider_resp(obj)

    @swagger.operation(
        notes="Deletes a provider",
        nickname="delprovider",
        responseMessages=[
            {
                "code": 204,
                "message": "Provider deleted",
            },
            {
                "code": 404,
                "message": "Provider not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
            {
                "code": 403,
                "message": "Access denied",
            },
        ],
        summary='TODO'
    )
    def delete(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"code": 404, "message": "Provider not found"}, 404

        if provider.nodes_count:
            msg = "Cannot delete provider while having nodes " \
                  "deployed on this provider"
            return {"code": 403, "message": msg}, 403

        db.delete(provider_id, "providers")
        salt = SaltHelper()
        salt.unregister_minion(provider.hostname)
        return {}, 204


class ProviderListResource(Resource):
    @swagger.operation(
        notes="Creates a new provider",
        nickname="postprovider",
        parameters=[
            {
                "name": "hostname",
                "description": "Hostname of the provider",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "docker_base_url",
                "description": "URL to Docker API, could be unix socket (e.g. unix:///var/run/docker.sock) for localhost or tcp (10.10.10.1:2375) for remote host",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "license_id",
                "description": "ID of the license",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_key",
                "description": "Public key for license",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password for license",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "license_password",
                "description": "License password",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created",
            },
            {
                "code": 400,
                "message": "Bad Request",
            },
            {
                "code": 403,
                "message": "Forbidden",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
    )
    def post(self):
        params = provider_req.parse_args()

        if params.license_id:
            # having license_id means provider is set as consumer;
            # therefore, we need to check few things:
            #
            # 1. make sure ``public_key``, ``public_password``,
            #    and ``license_password`` params are set
            # 2. make sure license exists in database
            # 3. license cannot be reuse
            # 4. if license exists, checks whether it's valid and not expired
            if not all([params.public_key, params.public_password,
                        params.license_password]):
                return {
                    "code": 400,
                    "message": "'public_key', 'public_password', and "
                               "'license_password' parameters cannot be "
                               "left blank when 'license_id' is set",
                }, 400

            # license cannot be reuse
            licensed_count = db.count_from_table(
                "providers", db.where("license_id") == params.license_id)
            if licensed_count:
                return {"code": 403, "message": "cannot reuse license"}, 403

            license = db.get(params.license_id, "licenses")
            if not license:
                return {"code": 400, "message": "invalid license ID"}, 400

            decoded_license = decode_signed_license(
                # license.decrypted_signed_license,
                # license.decrypted_public_key,
                # license.decrypted_public_password,
                # license.decrypted_license_password,
                license.signed_license,
                params.public_key,
                params.public_password,
                params.license_password,
            )
            # TODO: check expiration when oxd is updated
            if not decoded_license["valid"]:
                return {"code": 403, "message": "invalid license"}, 403
        else:
            # if we already have a master provider, rejects the request
            master_count = db.count_from_table(
                "providers", db.where("license_id"),
            )
            if master_count:
                return {
                    "code": 403,
                    "message": "cannot add another master provider",
                }, 403

        provider = Provider(fields=params)
        db.persist(provider, "providers")

        # register provider so we can execute weave commands later on
        salt = SaltHelper()
        salt.register_minion(provider.hostname)

        headers = {
            "Location": url_for("provider", provider_id=provider.id),
        }
        return format_provider_resp(provider), 201, headers

    @swagger.operation(
        notes="Gives provider info/state",
        nickname="listprovider",
        responseMessages=[
            {
              "code": 200,
              "message": "Provider list information",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
    )
    def get(self):
        obj_list = db.all("providers")
        return [format_provider_resp(item) for item in obj_list]
