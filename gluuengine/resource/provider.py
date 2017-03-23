# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import abort
from flask import request
from flask import url_for
from flask_restful import Resource

from ..extensions import db
from ..reqparser import GenericProviderReq
from ..reqparser import DigitalOceanProviderReq
from ..reqparser import AwsProviderReq
from ..model import GenericProvider
from ..model import DigitalOceanProvider
from ..model import AwsProvider
from ..model.provider import Provider

PROVIDER_TYPES = (
    'generic',
    'aws',
    'digitalocean',
    # 'google',
    #'rackspace',
)


class CreateProviderResource(Resource):
    def __init__(self):
        self.validate = {
            'generic': self.validate_generic,
            'aws': self.validate_aws,
            'digitalocean': self.validate_digitalocean,
            # 'google': self.validate_google,
        }
        self.model_cls = {
            'generic': GenericProvider,
            'digitalocean': DigitalOceanProvider,
            'aws': AwsProvider,
        }

    def validate_generic(self):
        data, errors = GenericProviderReq().load(request.form)
        return data, errors

    def validate_aws(self):
        data, errors = AwsProviderReq().load(request.form)
        return data, errors

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
        provider = model_cls(**data)
        db.session.add(provider)
        db.session.commit()

        headers = {
            "Location": url_for("provider", provider_id=provider.id),
        }
        return provider.as_dict(), 201, headers


class ProviderListResource(Resource):
    def get(self, provider_type=""):
        if not provider_type:
            # list all providers regardless their type
            return [provider.as_dict() for provider in Provider.query]

        if provider_type not in PROVIDER_TYPES:
            abort(404)

        # list specific provider by its type
        return [
            provider.as_dict()
            for provider in Provider.query.filter_by(driver=provider_type)
        ]


class ProviderResource(Resource):
    def get(self, provider_id):
        provider = Provider.query.get(provider_id)
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404
        return provider.as_dict()

    def delete(self, provider_id):
        provider = Provider.query.get(provider_id)
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        # if provider.is_in_use():
        #     msg = "Cannot delete provider while having nodes \
        #           deployed using this provider"
        #     return {"status": 403, "message": msg}, 403

        db.session.delete(provider)
        db.session.commit()
        return {}, 204
