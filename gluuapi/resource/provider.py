# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import request
from flask import url_for
# from flask import current_app
from flask_restful import Resource

from ..database import db
from ..reqparser import GenericProviderReq
from ..reqparser import DigitalOceanProviderReq
# from ..reqparser import EditProviderReq
from ..model import GenericProvider
from ..model import DigitalOceanProvider
# from ..helper import SaltHelper
# from ..helper import distribute_cluster_data
# from ..helper import ProviderHelper
# from ..utils import retrieve_signed_license
# from ..utils import decode_signed_license

PROVIDER_TYPES = ['generic', 'aws', 'digitalocean', 'google']


class CreateProviderResource(Resource):
    def __init__(self):
        self.validate = {
            'generic': self.validate_generic,
            'aws': self.validate_aws,
            'digitalocean': self.validate_digitalocean,
            'google': self.validate_google,
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

    def validate_aws(self):
        pass

    def validate_digitalocean(self):
        data, errors = DigitalOceanProviderReq().load(request.form)
        return data, errors

    def validate_google(self):
        pass

    def post(self, provider_type):
        if provider_type not in PROVIDER_TYPES:
            return {
                "status": 404,
                "message": "Provider type is not supported"
            }, 404

        data, errors = self.validate[provider_type]()
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        model_cls = self.model_cls[provider_type]
        provider = model_cls(data)
        db.persist(provider, "{}_providers".format(provider_type))

        headers = {
            "Location": url_for("provider", provider_type=provider_type,
                                provider_id=provider.id),
        }
        return provider.as_dict(), 201, headers


class ProviderListResource(Resource):
    def get(self, provider_type=""):
        if not provider_type:
            # list all providers by type
            generic_providers = db.all("generic_providers")
            digitalocean_providers = db.all("digitalocean_providers")

            # TODO: merge all providers
            providers = generic_providers + digitalocean_providers
            return [provider.as_dict() for provider in providers]

        # list specific provider types
        providers = db.all("{}_providers".format(provider_type))
        return [provider.as_dict() for provider in providers]


class ProviderResource(Resource):
    def __init__(self):
        self.validate = {
            'generic': self.validate_generic,
            'aws': self.validate_aws,
            'digitalocean': self.validate_digitalocean,
            'google': self.validate_google,
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

    def validate_aws(self):
        pass

    def validate_digitalocean(self):
        data, errors = DigitalOceanProviderReq().load(request.form)
        return data, errors

    def validate_google(self):
        pass

    def get(self, provider_type, provider_id):
        if provider_type not in PROVIDER_TYPES:
            return {
                "status": 404,
                "message": "Provider type is not supported"
            }, 404

        provider = db.get(provider_id, "{}_providers".format(provider_type))
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404
        return provider.as_dict()

    def delete(self, provider_type, provider_id):
        if provider_type not in PROVIDER_TYPES:
            return {
                "status": 404,
                "message": "Provider type is not supported"
            }, 404

        provider = db.get(provider_id, "{}_providers".format(provider_type))
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        if provider.is_in_use():
            msg = "Cannot delete provider while having nodes \
                  deployed using this provider"
            return {"status": 403, "message": msg}, 403

        db.delete(provider_id, "{}_providers".format(provider_type))
        return {}, 204

    def put(self, provider_type, provider_id):
        if provider_type not in PROVIDER_TYPES:
            return {
                "status": 404,
                "message": "Provider type is not supported"
            }, 404

        provider = db.get(provider_id, "{}_providers".format(provider_type))
        if not provider:
            return {"status": 404, "message": "Provider not found"}, 404

        data, errors = self.validate[provider_type]()
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        provider.populate(data)
        db.update(provider.id, provider, "{}_providers".format(provider_type))
        return provider.as_dict()


# class ProviderListResource(Resource):
#     def post(self):
#         data, errors = ProviderReq(
#             context={"docker_base_url": request.form.get("docker_base_url")}
#         ).load(request.form)

#         if errors:
#             return {
#                 "status": 400,
#                 "message": "Invalid data",
#                 "params": errors,
#             }, 400

#         app = current_app._get_current_object()
#         data["docker_cert_dir"] = app.config["DOCKER_CERT_DIR"]

#         master_num = db.count_from_table(
#             "providers", db.where("type") == "master",
#         )

#         # if requested provider is master and we already have
#         # a master provider, rejects the request
#         if data["type"] == "master" and master_num:
#             return {
#                 "status": 403,
#                 "message": "cannot add another master provider",
#             }, 403

#         # if requested provider is consumer, but we dont have
#         # a master provider yet, rejects the request
#         if data["type"] == "consumer" and not master_num:
#             return {
#                 "status": 403,
#                 "message": "requires a master provider registered first",
#             }, 403

#         if data["type"] == "consumer":
#             try:
#                 license_key = db.all("license_keys")[0]
#             except IndexError:
#                 license_key = None

#             if not license_key:
#                 return {
#                     "status": 403,
#                     "message": "requires a valid license key",
#                 }, 403

#             # check if metadata is already populated; if it's not,
#             # download signed license and populate the metadata;
#             # subsequent request will not be needed as we are
#             # removing the license count limitation
#             if not license_key.metadata:
#                 # download signed license from license server
#                 app.logger.info("downloading signed license")

#                 sl_resp = retrieve_signed_license(license_key.code)
#                 if not sl_resp.ok:
#                     err_msg = "unable to retrieve license from " \
#                               "https://license.gluu.org; code={} reason={}"
#                     app.logger.warn(err_msg.format(
#                         sl_resp.status_code,
#                         sl_resp.text,
#                     ))
#                     return {
#                         "status": 422,
#                         "message": "unable to retrieve license; "
#                                    "reason={}".format(sl_resp.text),
#                     }, 422

#                 signed_license = sl_resp.json()["license"]
#                 try:
#                     # generate metadata
#                     decoded_license = decode_signed_license(
#                         signed_license,
#                         license_key.decrypted_public_key,
#                         license_key.decrypted_public_password,
#                         license_key.decrypted_license_password,
#                     )
#                 except ValueError as exc:
#                     app.logger.warn("unable to generate metadata; "
#                                     "reason={}".format(exc))
#                     decoded_license = {"valid": False, "metadata": {}}
#                 finally:
#                     license_key.valid = decoded_license["valid"]
#                     license_key.metadata = decoded_license["metadata"]
#                     license_key.signed_license = signed_license
#                     db.update(license_key.id, license_key, "license_keys")

#         provider = Provider(fields=data)
#         provider.cluster_id = data["cluster_id"]
#         db.persist(provider, "providers")

#         prov_helper = ProviderHelper(provider, app)
#         prov_helper.setup(data["connect_delay"], data["exec_delay"])

#         headers = {
#             "Location": url_for("provider", provider_id=provider.id),
#         }
#         return provider.as_dict(), 201, headers

#     def get(self):
#         providers = db.all("providers")
#         return [provider.as_dict() for provider in providers]
