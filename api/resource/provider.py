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

from api.database import db
from api.reqparser import provider_req
from api.model import Provider


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
        return obj.as_dict()

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
        ],
        summary='TODO'
    )
    def delete(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"code": 404, "message": "Provider not found"}, 404

        db.delete(provider_id, "providers")
        return {}, 204


class ProviderListResource(Resource):
    @swagger.operation(
        notes="Creates a new provider",
        nickname="postprovider",
        parameters=[
            {
                "name": "name",
                "description": "Provider name",
                "required": True,
                "dataType": "string",
                "paramType": "form"
            },
            {
                "name": "base_url",
                "description": "URL to Docker API, could be unix socket or HTTP",
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
            },
        ],
    )
    def post(self):
        params = provider_req.parse_args()
        provider = Provider(fields=params)
        db.persist(provider, "providers")

        headers = {
            "Location": url_for("provider", provider_id=provider.id),
        }
        return provider.as_dict(), 201, headers

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
        return [item.as_dict() for item in obj_list]
