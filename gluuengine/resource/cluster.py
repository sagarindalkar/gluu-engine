# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import request
from flask import url_for
from flask_restful import Resource

from ..database import db
from ..model import Cluster
from ..reqparser import ClusterReq
from ..reqparser import ClusterUpdateReq
from ..utils import as_boolean


class ClusterResource(Resource):
    def get(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404
        return cluster.as_dict()

    def delete(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404

        if cluster.count_containers(state=""):
            msg = "Cannot delete cluster while having containers " \
                  "deployed on this cluster"
            return {"status": 403, "message": msg}, 403

        db.delete(cluster_id, "clusters")
        return {}, 204

    def put(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")

        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404

        external_ldap = as_boolean(request.form.get("external_ldap", False))

        data, errors = ClusterUpdateReq(
            context={"external_ldap": external_ldap},
        ).load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        # only set attr with user inputs
        for k, v in data.iteritems():
            setattr(cluster, k, v)

        db.update(cluster.id, cluster, "clusters")
        return cluster.as_dict()


class ClusterListResource(Resource):
    def get(self):
        clusters = db.all("clusters")
        return [cluster.as_dict() for cluster in clusters]

    def post(self):
        # limit to 1 cluster for now
        if len(db.all("clusters")) >= 1:
            return {"status": 403, "message": "cannot add more cluster"}, 403

        truthy = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
        falsy = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))
        external_ldap = request.form.get("external_ldap", False)
        if external_ldap in falsy:
            external_ldap = False
        elif external_ldap in truthy:
            external_ldap = True
        else:
            external_ldap = False

        data, errors = ClusterReq(
            context={"external_ldap": external_ldap}
        ).load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        cluster = Cluster(fields=data)
        db.persist(cluster, "clusters")

        headers = {
            "Location": url_for("cluster", cluster_id=cluster.id),
        }
        return cluster.as_dict(), 201, headers
