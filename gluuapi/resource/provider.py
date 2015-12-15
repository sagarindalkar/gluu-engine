# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import request
from flask import url_for
from flask import current_app
from flask_restful import Resource

from ..database import db
from ..reqparser import ProviderReq
from ..reqparser import EditProviderReq
from ..model import Provider
from ..helper import SaltHelper
from ..helper import distribute_cluster_data
from ..helper import ProviderHelper
from ..utils import retrieve_signed_license
from ..utils import decode_signed_license


def format_provider_resp(provider):
    item = provider.as_dict()
    item["type"] = provider.type
    return item


class ProviderResource(Resource):
    def get(self, provider_id):
        obj = db.get(provider_id, "providers")
        if not obj:
            return {"status": 404, "message": "Provider not found"}, 404
        return format_provider_resp(obj)

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
        distribute_cluster_data(current_app.config["DATABASE_URI"])
        return {}, 204

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
        data["docker_cert_dir"] = current_app.config["DOCKER_CERT_DIR"]
        provider.populate(data)
        db.update(provider.id, provider, "providers")

        prov_helper = ProviderHelper(provider, current_app._get_current_object())
        prov_helper.setup(data["connect_delay"], data["exec_delay"])
        return format_provider_resp(provider)


class ProviderListResource(Resource):
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

        app = current_app._get_current_object()
        data["docker_cert_dir"] = app.config["DOCKER_CERT_DIR"]

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

            # check if metadata is already populated; if it's not,
            # download signed license and populate the metadata;
            # subsequent request will not be needed as we are
            # removing the license count limitation
            if not license_key.metadata:
                # download signed license from license server
                app.logger.info("downloading signed license")

                sl_resp = retrieve_signed_license(license_key.code)
                if not sl_resp.ok:
                    err_msg = "unable to retrieve license from " \
                              "https://license.gluu.org; code={} reason={}"
                    app.logger.warn(err_msg.format(
                        sl_resp.status_code,
                        sl_resp.text,
                    ))
                    return {
                        "status": 422,
                        "message": "unable to retrieve license; "
                                   "reason={}".format(sl_resp.text),
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
                    app.logger.warn("unable to generate metadata; "
                                    "reason={}".format(exc))
                    decoded_license = {"valid": False, "metadata": {}}
                finally:
                    license_key.valid = decoded_license["valid"]
                    license_key.metadata = decoded_license["metadata"]
                    license_key.signed_license = signed_license
                    db.update(license_key.id, license_key, "license_keys")

        provider = Provider(fields=data)
        db.persist(provider, "providers")

        prov_helper = ProviderHelper(provider, app)
        prov_helper.setup(data["connect_delay"], data["exec_delay"])

        headers = {
            "Location": url_for("provider", provider_id=provider.id),
        }
        return format_provider_resp(provider), 201, headers

    def get(self):
        obj_list = db.all("providers")
        return [format_provider_resp(item) for item in obj_list]
