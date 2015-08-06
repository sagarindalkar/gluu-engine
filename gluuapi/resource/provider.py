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
from flask import request
from flask import url_for
from flask import current_app
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.reqparser import ProviderReq
from gluuapi.reqparser import EditProviderReq
from gluuapi.model import Provider
from gluuapi.helper import SaltHelper
from gluuapi.helper import WeaveHelper
from gluuapi.utils import retrieve_signed_license
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
        summary='Get a list of existing providers',
    )
    def get(self, provider_id):
        obj = db.get(provider_id, "providers")
        if not obj:
            return {"status": 404, "message": "Provider not found"}, 404
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
        summary='Delete existing provider',
    )
    def delete(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        if provider.nodes_count:
            msg = "Cannot delete provider while having nodes " \
                  "deployed on this provider"
            return {"status": 403, "message": msg}, 403

        db.delete(provider_id, "providers")
        salt = SaltHelper()
        salt.reject_minion(provider.hostname)
        return {}, 204

    @swagger.operation(
        notes="Updates a provider",
        nickname="editprovider",
        responseMessages=[
            {
                "code": 200,
                "message": "Provider updated",
            },
            {
                "code": 400,
                "message": "Bad Request",
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
                "description": "URL to Docker API (e.g. 'unix:///var/run/docker.sock' or 'https://ip:port')",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ssl_key",
                "description": "The contents of SSL client key file",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ssl_cert",
                "description": "The contents of SSL client cert file",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ca_cert",
                "description": "The contents of SSL CA cert file",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
        ],
        summary='Update existing provider',
    )
    def put(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        data, errors = EditProviderReq(
            context={
                "provider": provider,
                "docker_base_url": request.form.get("docker_base_url")
            },
        ).load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        data["type"] = provider.type
        provider.populate(data)
        db.update(provider.id, provider, "providers")

        # register provider so we can execute weave commands later on
        salt = SaltHelper()
        salt.register_minion(provider.hostname)

        cluster = db.all("clusters")[0]
        weave = WeaveHelper(
            provider, cluster, current_app.config["SALT_MASTER_IPADDR"],
        )
        weave.launch_async()
        return format_provider_resp(provider)


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
                "description": "URL to Docker API (e.g. 'unix:///var/run/docker.sock' or 'https://ip:port')",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "type",
                "description": "Provider type (either 'master' or 'consumer')",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ssl_key",
                "description": "The contents of SSL client key file",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ssl_cert",
                "description": "The contents of SSL client cert file",
                "required": False,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "ca_cert",
                "description": "The contents of SSL CA cert file",
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
                "code": 422,
                "message": "Unprocessable Entity",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Create a new provider',
    )
    def post(self):
        try:
            cluster = db.all("clusters")[0]
        except IndexError:
            cluster = None

        if not cluster:
            return {
                "status": 403,
                "message": "requires at least 1 cluster created first",
            }, 403

        data, errors = ProviderReq(
            context={"docker_base_url": request.form.get("docker_base_url")}
        ).load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        master_num = db.count_from_table(
            "providers", db.where("type") == "master",
        )

        # if requested provider is master and we already have
        # a master provider, rejects the request
        if data["type"] == "master" and master_num:
            return {
                "status": 403,
                "message": "cannot add another master provider",
            }, 403

        # if requested provider is consumer, but we dont have
        # a master provider yet, rejects the request
        if data["type"] == "consumer" and not master_num:
            return {
                "status": 403,
                "message": "requires a master provider registered first",
            }, 403

        if data["type"] == "consumer":
            try:
                license_key = db.all("license_keys")[0]
            except IndexError:
                license_key = None

            if not license_key:
                return {
                    "status": 403,
                    "message": "requires a valid license key",
                }, 403

            # download signed license from license server
            sl_resp = retrieve_signed_license(license_key.code)
            if not sl_resp.ok:
                err_msg = "unable to retrieve license from " \
                          "https://license.gluu.org; code={} reason={}"
                current_app.logger.warn(err_msg.format(
                    sl_resp.status_code,
                    sl_resp.text,
                ))
                return {
                    "status": 422,
                    "message": "unable to retrieve license",
                }, 422

            signed_license = sl_resp.json()["license"]
            try:
                # generate metadata
                decoded_license = decode_signed_license(
                    signed_license,
                    license_key.decrypted_public_key,
                    license_key.decrypted_public_password,
                    license_key.decrypted_license_password,
                )
            except ValueError as exc:
                current_app.logger.warn("unable to generate metadata; "
                                        "reason={}".format(exc))
                decoded_license = {"valid": False, "metadata": {}}
            finally:
                license_key.valid = decoded_license["valid"]
                license_key.metadata = decoded_license["metadata"]
                license_key.signed_license = signed_license
                db.update(license_key.id, license_key, "license_keys")

        provider = Provider(fields=data)
        db.persist(provider, "providers")

        weave = WeaveHelper(
            provider, cluster, current_app.config["SALT_MASTER_IPADDR"],
        )
        weave.launch_async()

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
        summary='Get existing provider',
    )
    def get(self):
        obj_list = db.all("providers")
        return [format_provider_resp(item) for item in obj_list]
