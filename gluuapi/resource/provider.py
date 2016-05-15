# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import abort
from flask import request
from flask import url_for
from flask_restful import Resource

from ..database import db
from ..reqparser import GenericProviderReq
from ..reqparser import DigitalOceanProviderReq
from ..model import GenericProvider
from ..model import DigitalOceanProvider

PROVIDER_TYPES = (
    'generic',
    # 'aws',
    'digitalocean',
    # 'google',
)


class CreateProviderResource(Resource):
    def __init__(self):
        self.validate = {
            'generic': self.validate_generic,
            # 'aws': self.validate_aws,
            'digitalocean': self.validate_digitalocean,
            # 'google': self.validate_google,
        }
        self.model_cls = {
            'generic': GenericProvider,
            # 'aws': self.validate_aws,
            'digitalocean': DigitalOceanProvider,
            # 'google': self.validate_google,
        }

    def validate_generic(self):
        data, errors = GenericProviderReq().load(request.form)
        return data, errors

    # def validate_aws(self):
    #     pass

    def validate_digitalocean(self):
        data, errors = DigitalOceanProviderReq().load(request.form)
        return data, errors

    # def validate_google(self):
    #     pass

    def post(self, provider_type):
        if provider_type not in PROVIDER_TYPES:
            abort(404)

        data, errors = self.validate[provider_type]()
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        model_cls = self.model_cls[provider_type]
        provider = model_cls(data)
        db.persist(provider, "providers")

        headers = {
            "Location": url_for("provider", provider_id=provider.id),
        }
        return provider.as_dict(), 201, headers


class ProviderListResource(Resource):
    def get(self, provider_type=""):
        if not provider_type:
            # list all providers by type
            providers = db.all("providers")
            return [provider.as_dict() for provider in providers]

        if provider_type not in PROVIDER_TYPES:
            abort(404)

        # list specific provider types
        providers = db.search_from_table("providers", db.where('driver') == provider_type)
        return [provider.as_dict() for provider in providers]


class ProviderResource(Resource):
    def __init__(self):
        self.validate = {
            'generic': self.validate_generic,
            # 'aws': self.validate_aws,
            'digitalocean': self.validate_digitalocean,
            # 'google': self.validate_google,
        }

    def validate_generic(self):
        data, errors = GenericProviderReq().load(request.form)
        return data, errors

    # def validate_aws(self):
    #     pass

    def validate_digitalocean(self):
        data, errors = DigitalOceanProviderReq().load(request.form)
        return data, errors

    # def validate_google(self):
    #     pass

    def get(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404
        return provider.as_dict()

    def delete(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        if provider.is_in_use():
            msg = "Cannot delete provider while having nodes \
                  deployed using this provider"
            return {"status": 403, "message": msg}, 403

        db.delete(provider_id, 'providers')
        return {}, 204

    def put(self, provider_id):
        provider = db.get(provider_id, "providers")
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        data, errors = self.validate[provider.driver]()
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        provider.populate(data)
        db.update(provider.id, provider, "providers")
        return provider.as_dict()
