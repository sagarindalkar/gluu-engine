# -*- coding: utf-8 -*-
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
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.model import License
from gluuapi.reqparser import license_req
from gluuapi.reqparser import edit_license_req
from gluuapi.utils import decode_signed_license
from gluuapi.utils import retrieve_signed_license


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
            return {"code": 404, "message": "License not found"}, 404
        return format_license_resp(license)

    @swagger.operation(
        notes="",
        nickname="editlicense",
        parameters=[
            {
                "name": "public_key",
                "description": "Public key for license (won't be stored)",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password for license",
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
                "message": "License Updated",
            },
            {
                "code": 400,
                "message": "Bad Request",
            },
            {
                "code": 404,
                "message": "License Not Found",
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
        summary="Update existing license",
    )
    def put(self, license_id):
        params = edit_license_req.parse_args()

        license = db.get(license_id, "licenses")
        if not license:
            return {"code": 404, "message": "license not found"}, 404

        try:
            decoded_license = decode_signed_license(
                license.signed_license,
                params.public_key,
                params.public_password,
                params.license_password,
            )
        except ValueError:
            return {
                "code": 422,
                "message": "invalid 'public_key', 'public_password', or 'license_password' value",
            }, 422

        if not decoded_license["valid"]:
            return {
                "code": 422,
                "message": "invalid 'public_key', 'public_password', or 'license_password' value",
            }, 422

        params.valid = decoded_license["valid"]
        params.metadata = decoded_license["metadata"]
        params.code = license.code
        params.signed_license = license.signed_license
        params.billing_email = license.billing_email
        params.id = license.id

        license.populate(params)
        db.update(license.id, license, "licenses")
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
            return {"code": 404, "message": "License not found"}, 404

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
                "name": "public_key",
                "description": "Public key for license",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password for license",
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
        params = license_req.parse_args()

        resp = retrieve_signed_license(params.code)
        if not resp.ok:
            current_app.logger.warn(resp.text)
            return {"code": 422, "message": "unable to retrieve license"}, 422

        params.signed_license = resp.json()["license"]

        try:
            decoded_license = decode_signed_license(
                params.signed_license,
                params.public_key,
                params.public_password,
                params.license_password,
            )
        except ValueError:
            # when generating license's metadata, we dont care whether creds
            # are invalid since we can re-generate the metadata in
            # separate API call; see ``LicenseResource.put``
            pass
        else:
            params.valid = decoded_license["valid"]
            params.metadata = decoded_license["metadata"]

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
