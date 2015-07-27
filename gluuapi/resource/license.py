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
from flask import request
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.model import LicenseKey
from gluuapi.reqparser import LicenseKeyReq


def format_license_key_resp(obj):
    resp = obj.as_dict()
    resp["public_key"] = obj.decrypted_public_key
    resp["public_password"] = obj.decrypted_public_password
    resp["license_password"] = obj.decrypted_license_password
    return resp

class LicenseKeyListResource(Resource):
    @swagger.operation(
        notes="",
        nickname="postlicensekey",
        parameters=[
            {
                "name": "name",
                "description": "Decriptive name",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "code",
                "description": "License code retrieved from license server",
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
                "code": 403,
                "message": "Forbidden",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary="Create license key",
    )
    def post(self):
        if len(db.all("license_keys")):
            return {
                "status": 403,
                "message": "cannot add more license key",
            }, 403

        data, errors = LicenseKeyReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400
        license_key = LicenseKey(fields=data)
        db.persist(license_key, "license_keys")

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return format_license_key_resp(license_key), 201, headers

    @swagger.operation(
        notes='Gives license keys info/state',
        nickname='listlicensekey',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License key information",
            },
            {
                "code": 404,
                "message": "License key not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get a list of existing license keys",
    )
    def get(self):
        license_keys = db.all("license_keys")
        return [format_license_key_resp(license_key)
                for license_key in license_keys]


class LicenseKeyResource(Resource):
    @swagger.operation(
        notes='Gives license key info/state',
        nickname='licensekey',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "License license_key information",
            },
            {
                "code": 404,
                "message": "License key not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary="Get a list of existing license key",
    )
    def get(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "license key not found"}, 404
        return format_license_key_resp(license_key)

    @swagger.operation(
        notes="",
        nickname="putlicensekey",
        parameters=[
            {
                "name": "name",
                "description": "Decriptive name",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
            {
                "name": "code",
                "description": "License code retrieved from license server",
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
        summary="Update license key",
    )
    def put(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "license key not found"}, 404

        data, errors = LicenseKeyReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400
        license_key.populate(data)
        db.update(license_key_id, license_key, "license_keys")
        return format_license_key_resp(license_key)

    @swagger.operation(
        notes="Delete a license key",
        nickname="dellicensekey",
        responseMessages=[
            {
                "code": 204,
                "message": "License key deleted",
            },
            {
                "code": 404,
                "message": "License key not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Delete existing license key'
    )
    def delete(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "License key not found"}, 404

        db.delete(license_key_id, "license_keys")
        return {}, 204
