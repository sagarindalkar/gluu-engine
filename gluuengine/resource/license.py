# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

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
from ..utils import retrieve_signed_license
from ..utils import decode_signed_license


def format_license_key_resp(obj):
    resp = obj.as_dict()
    resp["public_key"] = obj.decrypted_public_key
    # resp["public_password"] = obj.decrypted_public_password
    # resp["license_password"] = obj.decrypted_license_password
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

        license_key = LicenseKey(fields=data)
        license_key, err = self.populate_license(license_key)
        if err:
            return {
                "status": 422,
                "message": "unable to retrieve license; reason={}".format(err),
            }, 422

        db.persist(license_key, "license_keys")
        distribute_cluster_data(current_app.config["SHARED_DATABASE_URI"],
                                current_app._get_current_object())

        headers = {
            "Location": url_for("licensekey", license_key_id=license_key.id),
        }
        return format_license_key_resp(license_key), 201, headers

    def get(self):
        license_keys = db.all("license_keys")
        return [format_license_key_resp(license_key)
                for license_key in license_keys]

    def populate_license(self, license_key):
        err_msg = ""

        # download signed license from license server
        current_app.logger.info("downloading signed license")

        sl_resp = retrieve_signed_license(license_key.code)
        if not sl_resp.ok:
            err_msg = "unable to retrieve license from " \
                      "https://license.gluu.org; code={} reason={}"
            current_app.logger.warn(err_msg.format(
                sl_resp.status_code,
                sl_resp.text,
            ))
            return license_key, err_msg

        signed_license = sl_resp.json()[0]["license"]
        try:
            # generate metadata
            decoded_license = decode_signed_license(
                signed_license,
                license_key.decrypted_public_key,
                license_key.decrypted_public_password,
                license_key.decrypted_license_password,
            )
        except ValueError as exc:
            current_app.logger.warn("unable to generate metadata; "
                                    "reason={}".format(exc))
            decoded_license = {"valid": False, "metadata": {}}
        finally:
            license_key.valid = decoded_license["valid"]
            license_key.metadata = decoded_license["metadata"]
            license_key.signed_license = signed_license
            return license_key, err_msg


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

        data, errors = LicenseKeyReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400
        license_key.populate(data)

        try:
            # try to recalculate the metadata
            decoded_license = decode_signed_license(
                license_key.signed_license,
                license_key.decrypted_public_key,
                license_key.decrypted_public_password,
                license_key.decrypted_license_password,
            )
        except RuntimeError as exc:
            current_app.logger.warn("unable to generate metadata; "
                                    "reason={}".format(exc))
            decoded_license = {"valid": False, "metadata": {}}
        finally:
            license_key.valid = decoded_license["valid"]
            license_key.metadata = decoded_license["metadata"]
            db.update(license_key.id, license_key, "license_keys")

        # if worker nodes have disabled oxAuth and oxIdp containers and license
        # key is not expired, try to re-enable the containers
        if not license_key.expired:
            mc = Machine()

            for worker_node in license_key.get_workers():
                weave = Weave(
                    worker_node, current_app._get_current_object(),
                )
                for type_ in ["oxauth", "oxidp"]:
                    containers = worker_node.get_containers(
                        type_=type_, state=STATE_DISABLED,
                    )

                    for container in containers:
                        container.state = STATE_SUCCESS
                        db.update(container.id, container, "containers")
                        mc.ssh(worker_node.name, "docker restart {}".format(container.cid))
                        weave.dns_add(container.cid, container.hostname)

        distribute_cluster_data(current_app.config["SHARED_DATABASE_URI"],
                                current_app._get_current_object())
        return format_license_key_resp(license_key)

    def delete(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "License key not found"}, 404

        if license_key.count_workers():
            msg = "Cannot delete license key while having worker nodes"
            return {"status": 403, "message": msg}, 403

        db.delete(license_key_id, "license_keys")
        distribute_cluster_data(current_app.config["SHARED_DATABASE_URI"],
                                current_app._get_current_object())
        return {}, 204
