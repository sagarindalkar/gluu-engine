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

# import requests
from flask import url_for
from flask_restful import Resource
from flask_restful_swagger import swagger

from gluuapi.database import db
from gluuapi.model import License
from gluuapi.reqparser import license_req


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


# TODO: remove this when https://license.gluu.org/rest/generate is available
DUMMY_SIGNED_LICENSE = (
    "rO0ABXNyADFuZXQubmljaG9sYXN3aWxsaWFtcy5qYXZhLmxpY2Vuc2luZy5TaWduZWRMaWNlb"
    "nNlioT/n36yaoQCAAJbAA5saWNlbnNlQ29udGVudHQAAltCWwAQc2lnbmF0dXJlQ29udGVudH"
    "EAfgABeHB1cgACW0Ks8xf4BghU4AIAAHhwAAAAsH5UJYfDckbmYyhwgwZEdIBrWrPyWAZz/XK"
    "LcjFHfGP9Z0ijcWSM4KfwVvQdixsrDXUI7LZGFw3NYvkXBc6PRAQnZc2cXCkk+ew8SjW+cF8s"
    "ECF/GLwhQ+O2vszme07xZfnEkzVXDgtMGpkHuNXplWBV7TDHP0VAK2OMlHMlM2/7Y7kTIAdrY"
    "Rk4RKSV91cIrYWO8j5B937jlnlAIK+vnHqSMawdcwEC9h9vn2nPNs3RdXEAfgADAAABAEC8eq"
    "Bc+OplB6GSY9NSE/nSAiyVz+clVpM3bgrGDBasBRGgyQPLu/u0+f4/y0V41SfVpSeqKXX+9Jq"
    "tPEIjnZGB2vSIyZzoCm7DaDwQjTN3GME4qx91n33NW+48mWNL1qfY6gIRwwmSRDc0BOQLz27H"
    "C+QzGsX5Hp+I1HmkcUd0gHHBDrQuhRYw4lglcoTpuX5L4lMNVRGSvbpThpFbbCd1VfUqi9/AF"
    "hEGZKlpPVQdVYyIpaJwIOrNZu4HfS5H4IJZQ+FlnisvZwEmEVMaEGLvvfxxPXlmpVdhbTnvO7"
    "mXi4rVog3clMg7dHQLgZwRaeRfZHEHWFvQ8eW6de7FK4E="
)


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
                "name": "name",
                "description": "License name",
                "required": False,
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
                "code": 500,
                "message": "Internal Server Error",
            }
        ],
        summary="Create a new license",
    )
    def post(self):
        params = license_req.parse_args()
        params.signed_license = DUMMY_SIGNED_LICENSE

        # # FIXME: request for a license from https://license.gluu.org
        # resp = requests.post(
        #     "https://license.gluu.org/rest/generate",
        #     params={"licenseId": params.code},
        # )
        # if resp.ok:
        #     params.signed_license = resp.json()["license"]

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
