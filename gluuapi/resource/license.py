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
# from datetime import timedelta
from flask import url_for
from flask import current_app
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.model import License
from gluuapi.reqparser import license_req
from gluuapi.utils import decode_signed_license
from gluuapi.utils import retrieve_signed_license
# from gluuapi.utils import timestamp_millis
# from gluuapi.utils import timestamp_millis_to_datetime
# from gluuapi.utils import datetime_to_timestamp_millis


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
        return license.as_dict()


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
                "name": "billing_email",
                "description": "Email address where expiration reminder will be sent to",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "public_key",
                "description": "Public key for license (won't be stored)",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "public_password",
                "description": "Public password for license (won't be stored)",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "license_password",
                "description": "License password (won't be stored)",
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

        # ``signed_license`` might be a null value
        if not params.signed_license:
            return {"code": 422, "message": "invalid signed license (null value)"}, 422

        decoded_license = decode_signed_license(
            params.signed_license,
            params.public_key,
            params.public_password,
            params.license_password,
        )
        params.valid = decoded_license["valid"]
        params.metadata = decoded_license["metadata"]

        # # TODO: remove this dummy expiration_date
        # DUMMY_EXPIRATION_DATE = datetime_to_timestamp_millis(
        #     timestamp_millis_to_datetime(timestamp_millis()) - timedelta(days=7)
        # )
        # params.metadata["expiration_date"] = DUMMY_EXPIRATION_DATE

        license = License(fields=params)
        db.persist(license, "licenses")

        headers = {
            "Location": url_for("license", license_id=license.id),
        }
        return license.as_dict(), 201, headers

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
        return [license.as_dict() for license in licenses]
