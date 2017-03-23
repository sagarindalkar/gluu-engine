# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import request
from flask import url_for
from flask_restful import Resource

from ..extensions import db
from ..model import Cluster
from ..reqparser import ClusterReq


class ClusterResource(Resource):
    def get(self, cluster_id):
        cluster = Cluster.query.get(cluster_id)
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404
        return cluster.as_dict()

    def delete(self, cluster_id):
        cluster = Cluster.query.get(cluster_id)
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404
        if cluster.count_containers(state=""):
            msg = "Cannot delete cluster while having containers " \
                  "deployed on this cluster"
            return {"status": 403, "message": msg}, 403

        db.session.delete(cluster)
        db.session.commit()
        return {}, 204


class ClusterListResource(Resource):
    def get(self):
        return [cluster.as_dict() for cluster in Cluster.query]

    def post(self):
        # limit to 1 cluster for now
        if Cluster.query.count():
            return {"status": 403, "message": "cannot add more cluster"}, 403

        data, errors = ClusterReq().load(request.form)

        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        cluster = Cluster(**data)
        db.session.add(cluster)
        db.session.commit()

        headers = {
            "Location": url_for("cluster", cluster_id=cluster.id),
        }
        return cluster.as_dict(), 201, headers
