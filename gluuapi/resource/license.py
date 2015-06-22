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
from flask import current_app
from flask import request
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.model import License
from gluuapi.model import LicenseCredential
from gluuapi.reqparser import LicenseReq
from gluuapi.reqparser import CredentialReq
from gluuapi.utils import retrieve_signed_license
from gluuapi.utils import decode_signed_license


def format_license_resp(obj):
    resp = obj.as_dict()
    resp["expired"] = obj.expired
    return resp


class LicenseResource(Resource):
    @swagger.operation(
        notes='Gives license info/state',
        nickname='license',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License information",
            },
            {
                "code": 404,
                "message": "License not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get existing license",
    )
    def get(self, license_id):
        license = db.get(license_id, "licenses")
        if not license:
            return {"status": 404, "message": "License not found"}, 404
        return format_license_resp(license)

    @swagger.operation(
        notes="Deletes a license",
        nickname="dellicense",
        responseMessages=[
            {
                "code": 204,
                "message": "License deleted",
            },
            {
                "code": 404,
                "message": "License not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='TODO'
    )
    def delete(self, license_id):
        license = db.get(license_id, "licenses")
        if not license:
            return {"status": 404, "message": "License not found"}, 404

        db.delete(license_id, "licenses")
        return {}, 204


class LicenseListResource(Resource):
    @swagger.operation(
        notes="",
        nickname="postlicense",
        parameters=[
            {
                "name": "code",
                "description": "License code (licenseId) retrieved from https://license.gluu.org",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "credential_id",
                "description": "Credential ID to use (useful for generating metadata)",
                "required": True,
                "dataType": "string",
                "paramType": "form",
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
                "code": 422,
                "message": "Unprocessable Entity",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary="Create a new license",
    )
    def post(self):
        data, errors = LicenseReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        params = data["params"]
        credential = data["context"]["credential"]

        resp = retrieve_signed_license(params["code"])
        if not resp.ok:
            current_app.logger.warn(resp.text)
            return {
                "status": 422,
                "message": "unable to retrieve license",
            }, 422

        params["signed_license"] = resp.json()["license"]

        try:
            decoded_license = decode_signed_license(
                params["signed_license"],
                credential.decrypted_public_key,
                credential.decrypted_public_password,
                credential.decrypted_license_password,
            )
        except ValueError as exc:
            current_app.logger.warn("unable to generate metadata; "
                                    "reason={}".format(exc))
        else:
            params["valid"] = decoded_license["valid"]
            params["metadata"] = decoded_license["metadata"]

        license = License(fields=params)
        db.persist(license, "licenses")

        headers = {
            "Location": url_for("license", license_id=license.id),
        }
        return format_license_resp(license), 201, headers

    @swagger.operation(
        notes='Gives license info/state',
        nickname='listlicense',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License list information",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get a list of existing licenses",
    )
    def get(self):
        licenses = db.all("licenses")
        return [format_license_resp(license) for license in licenses]


def format_credential_resp(obj):
    resp = obj.as_dict()
    resp["public_key"] = obj.decrypted_public_key
    resp["public_password"] = obj.decrypted_public_password
    resp["license_password"] = obj.decrypted_license_password
    return resp

class LicenseCredentialListResource(Resource):
    @swagger.operation(
        notes="",
        nickname="postlicensecred",
        parameters=[
            {
                "name": "name",
                "description": "Decriptive name",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "public_key",
                "description": "Public key",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "license_password",
                "description": "License password",
                "required": True,
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
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary="Create license credential",
    )
    def post(self):
        data, errors = CredentialReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400
        credential = LicenseCredential(fields=data)
        db.persist(credential, "license_credentials")

        headers = {
            "Location": url_for("licensecred", credential_id=credential.id),
        }
        return format_credential_resp(credential), 201, headers

    @swagger.operation(
        notes='Gives license credentials info/state',
        nickname='listlicensecred',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License credential information",
            },
            {
                "code": 404,
                "message": "License credential not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get a list of existing license credentials",
    )
    def get(self):
        credentials = db.all("license_credentials")
        return [format_credential_resp(credential)
                for credential in credentials]


class LicenseCredentialResource(Resource):
    @swagger.operation(
        notes='Gives license credential info/state',
        nickname='licensecred',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License credential information",
            },
            {
                "code": 404,
                "message": "License credential not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get a list of existing license credential",
    )
    def get(self, credential_id):
        credential = db.get(credential_id, "license_credentials")
        if not credential:
            return {"status": 404, "message": "Credential not found"}, 404
        return format_credential_resp(credential)

    @swagger.operation(
        notes="",
        nickname="putlicensecred",
        parameters=[
            {
                "name": "name",
                "description": "Decriptive name",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "public_key",
                "description": "Public key",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "license_password",
                "description": "License password",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
        ],
        responseMessages=[
            {
                "code": 200,
                "message": "OK",
            },
            {
                "code": 400,
                "message": "Bad Request",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary="Update license credential",
    )
    def put(self, credential_id):
        credential = db.get(credential_id, "license_credentials")
        if not credential:
            return {"status": 404, "message": "Credential not found"}, 404

        # params = license_cred_req.parse_args()
        data, errors = CredentialReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400
        credential.populate(data)
        db.update(credential_id, credential, "license_credentials")

        for license in credential.get_license_objects():
            try:
                decoded_license = decode_signed_license(
                    license.signed_license,
                    credential.decrypted_public_key,
                    credential.decrypted_public_password,
                    credential.decrypted_license_password,
                )
            except ValueError as exc:
                current_app.logger.warn("unable to generate metadata; "
                                        "reason={}".format(exc))
                license.valid = False
                license.metadata = {}
            else:
                license.valid = decoded_license["valid"]
                license.metadata = decoded_license["metadata"]
            finally:
                db.update(license.id, license, "licenses")
        return format_credential_resp(credential)

    @swagger.operation(
        notes="Delete a license credential",
        nickname="dellicensecred",
        responseMessages=[
            {
                "code": 204,
                "message": "License credential deleted",
            },
            {
                "code": 404,
                "message": "License credential not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Delete existing license credential'
    )
    def delete(self, credential_id):
        credential = db.get(credential_id, "license_credentials")
        if not credential:
            return {"status": 404, "message": "License credential not found"}, 404

        db.delete(credential_id, "license_credentials")
        return {}, 204
