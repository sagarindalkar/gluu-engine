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


def format_cluster_resp(cluster):
    item = cluster.as_dict()
    item["ldap_containers"] = [container.id for container in cluster.get_containers(type_="ldap")]
    item["oxauth_containers"] = [container.id for container in cluster.get_containers(type_="oxauth")]
    item["oxtrust_containers"] = [container.id for container in cluster.get_containers(type_="oxtrust")]
    item["oxidp_containers"] = [container.id for container in cluster.get_containers(type_="oxidp")]
    item["nginx_containers"] = [container.id for container in cluster.get_containers(type_="nginx")]
    return item


class ClusterResource(Resource):
    def get(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404
        return format_cluster_resp(cluster)

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


class ClusterListResource(Resource):
    def get(self):
        clusters = db.all("clusters")
        return [format_cluster_resp(cluster) for cluster in clusters]

    def post(self):
        # limit to 1 cluster for now
        if len(db.all("clusters")) >= 1:
            return {"status": 403, "message": "cannot add more cluster"}, 403

        data, errors = ClusterReq().load(request.form)
        if errors:
            return {
                "status": 400,
                "message": "Invalid data",
                "params": errors,
            }, 400

        cluster = Cluster(fields=data)
        db.persist(cluster, "clusters")

        headers = {
            "Location": url_for("clusterresource", cluster_id=cluster.id),
        }
        return format_cluster_resp(cluster), 201, headers
