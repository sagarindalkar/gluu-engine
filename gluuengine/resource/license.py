# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from crochet import run_in_reactor
from flask import url_for
from flask import request
from flask import current_app
from flask_restful import Resource

from ..database import db
from ..model import LicenseKey
from ..reqparser import LicenseKeyReq
from ..model import STATE_DISABLED
from ..model import STATE_SUCCESS
from ..helper import distribute_cluster_data
from ..weave import Weave
from ..machine import Machine
from ..utils import retrieve_current_date
from ..utils import populate_license


def format_license_key_resp(obj):
    resp = obj.as_dict()
    resp["public_key"] = obj.decrypted_public_key
    return resp


class LicenseKeyListResource(Resource):
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

        license_key = LicenseKey(data)

        current_app.logger.info("downloading signed license")
        license_key, err = populate_license(license_key)

        if err:
            return {"status": 422, "message": err}, 422

        if license_key.expired:
            return {
                "status": 403,
                "message": "expired license is not allowed",
            }, 403

        if license_key.mismatched:
            return {
                "status": 403,
                "message": "non-Docker Edition product license is not allowed",
            }, 403

        if not license_key.is_active:
            return {
                "status": 403,
                "message": "non-active license is not allowed",
            }, 403

        license_key.import_data({"updated_at": retrieve_current_date()})
        db.persist(license_key, "license_keys"),

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return format_license_key_resp(license_key), 201, headers

    def get(self):
        license_keys = db.all("license_keys")
        return [format_license_key_resp(license_key)
                for license_key in license_keys]


class LicenseKeyResource(Resource):
    def get(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "license key not found"}, 404
        return format_license_key_resp(license_key)

    def put(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "license key not found"}, 404

        current_app.logger.info("downloading signed license")
        license_key, err = populate_license(license_key)

        if err:
            return {"status": 422, "message": err}, 422

        if license_key.expired:
            return {
                "status": 403,
                "message": "expired license is not allowed",
            }, 403

        if license_key.mismatched:
            return {
                "status": 403,
                "message": "non-Docker Edition product license is not allowed",
            }, 403

        if not license_key.is_active:
            return {
                "status": 403,
                "message": "non-active license is not allowed",
            }, 403

        license_key.updated_at = retrieve_current_date()
        db.update(license_key.id, license_key, "license_keys")

        # TODO: review if this is necessary in API call
        self._enable_containers(
            license_key, current_app._get_current_object()
        )

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return format_license_key_resp(license_key), 200, headers

    def delete(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "License key not found"}, 404

        if license_key.count_workers():
            msg = "Cannot delete license key while having worker nodes"
            return {"status": 403, "message": msg}, 403

        db.delete(license_key_id, "license_keys")
        return {}, 204

    @run_in_reactor
    def _enable_containers(self, license_key, app):
        mc = Machine()

        for worker_node in license_key.get_workers():
            weave = Weave(worker_node, app)
            containers = worker_node.get_containers(
                type_="oxauth", state=STATE_DISABLED,
            )

            for container in containers:
                container.state = STATE_SUCCESS
                db.update(container.id, container, "containers")
                mc.ssh(
                    worker_node.name,
                    "docker restart {}".format(container.cid),
                )
                weave.dns_add(container.cid, container.hostname)
                weave.dns_add(
                    container.cid,
                    "{}.weave.local".format("oxauth"),
                )
            distribute_cluster_data(app, worker_node)
