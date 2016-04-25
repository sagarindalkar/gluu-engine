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
from ..helper import WeaveHelper
from ..helper import distribute_cluster_data
from ..utils import decode_signed_license

def format_license_key_resp(obj):
    resp = obj.as_dict()
    resp["public_key"] = obj.decrypted_public_key
    resp["public_password"] = obj.decrypted_public_password
    resp["license_password"] = obj.decrypted_license_password
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
        db.persist(license_key, "license_keys")
        distribute_cluster_data(current_app.config["DATABASE_URI"])

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

        # if worker nodes have disabled oxAuth containers and license
        # key is not expired, try to re-enable the containers
        if not license_key.expired:
            for worker_node in license_key.get_workers():
                weave = WeaveHelper(
                    worker_node, current_app._get_current_object(),
                )
                for type_ in ["oxauth", "oxidp"]:
                    containers = worker_node.get_containers(
                        type_=type_, state=STATE_DISABLED,
                    )

                    for container in containers:
                        container.state = STATE_SUCCESS
                        db.update(container.id, container, "containers")
                        cidr = "{}/{}".format(container.weave_ip,
                                              container.weave_prefixlen)
                        weave.attach(cidr, container.id)
                        weave.dns_add(container.id, container.domain_name)

        distribute_cluster_data(current_app.config["DATABASE_URI"])
        return format_license_key_resp(license_key)

    def delete(self, license_key_id):
        license_key = db.get(license_key_id, "license_keys")
        if not license_key:
            return {"status": 404, "message": "License key not found"}, 404

        if len(license_key.get_workers()):
            msg = "Cannot delete license key while having worker nodes"
            return {"status": 403, "message": msg}, 403

        db.delete(license_key_id, "license_keys")
        distribute_cluster_data(current_app.config["DATABASE_URI"])
        return {}, 204
