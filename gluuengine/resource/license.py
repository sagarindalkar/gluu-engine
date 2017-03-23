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
from ..machine import Machine
from ..utils import retrieve_current_date
from ..utils import populate_license


class LicenseKeyListResource(Resource):
    def post(self):
        if LicenseKey.query.count():
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

        license_key = LicenseKey(**data)

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
        db.session.add(license_key)
        db.session.commit()

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return license_key.as_dict(), 201, headers

    def get(self):
        return [license_key.as_dict() for license_key in LicenseKey.query]


class LicenseKeyResource(Resource):
    def get(self, license_key_id):
        license_key = LicenseKey.query.get(license_key_id)
        if not license_key:
            return {"status": 404, "message": "license key not found"}, 404
        return license_key.as_dict()

    def put(self, license_key_id):
        license_key = LicenseKey.query.get(license_key_id)
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
        db.session.add(license_key)
        db.session.commit()

        # TODO: review if this is necessary in API call
        self._enable_containers(
            license_key, current_app._get_current_object()
        )

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return license_key.as_dict(), 200, headers

    def delete(self, license_key_id):
        license_key = LicenseKey.query.get(license_key_id)
        if not license_key:
            return {"status": 404, "message": "License key not found"}, 404

        if license_key.count_workers():
            msg = "Cannot delete license key while having worker nodes"
            return {"status": 403, "message": msg}, 403

        db.session.delete(license_key)
        db.session.commit()
        return {}, 204

    @run_in_reactor
    def _enable_containers(self, license_key, app):
        mc = Machine()

        with app.app_context():
            for worker_node in license_key.get_workers():
                containers = worker_node.get_containers(
                    type_="oxauth", state=STATE_DISABLED,
                )

                for container in containers:
                    container.state = STATE_SUCCESS
                    db.session.add(container)
                    db.session.commit()
                    mc.ssh(
                        worker_node.name,
                        "docker restart {}".format(container.cid),
                    )
