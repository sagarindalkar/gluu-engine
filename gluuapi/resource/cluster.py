# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask import current_app
from flask import request
from flask import url_for
from flask_restful import Resource
from flask_restful_swagger import swagger

from ..database import db
from ..helper import distribute_cluster_data
from ..model import GluuCluster
from ..reqparser import ClusterReq


def format_cluster_resp(cluster):
    item = cluster.as_dict()
    item["ldap_nodes"] = [node.id for node in cluster.get_ldap_objects()]
    item["httpd_nodes"] = [node.id for node in cluster.get_httpd_objects()]
    item["oxauth_nodes"] = [node.id for node in cluster.get_oxauth_objects()]
    item["oxtrust_nodes"] = [node.id for node in cluster.get_oxtrust_objects()]
    return item


class Cluster(Resource):
    @swagger.operation(
        notes='Gives cluster info/state',
        nickname='getcluster',
        parameters=[],
        responseMessages=[
            {
                "code": 200,
                "message": "List cluster information",
            },
            {
                "code": 404,
                "message": "Cluster not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary='Get a list of existing clusters',
    )
    def get(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404
        return format_cluster_resp(cluster)

    @swagger.operation(
        notes='delete a cluster',
        nickname='delcluster',
        parameters=[],
        responseMessages=[
            {
                "code": 204,
                "message": "Cluster deleted"
            },
            {
                "code": 403,
                "message": "Forbidden",
            },
            {
                "code": 404,
                "message": "Cluster not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Delete existing cluster',
    )
    def delete(self, cluster_id):
        cluster = db.get(cluster_id, "clusters")
        if not cluster:
            return {"status": 404, "message": "Cluster not found"}, 404

        if cluster.nodes_count:
            msg = "Cannot delete cluster while having nodes " \
                  "deployed on this cluster"
            return {"status": 403, "message": msg}, 403

        db.delete(cluster_id, "clusters")
        distribute_cluster_data(current_app.config["DATABASE_URI"])
        return {}, 204


class ClusterList(Resource):
    @swagger.operation(
        notes='Gives cluster info/state',
        nickname='listcluster',
        parameters=[],
        responseMessages=[
            {
              "code": 200,
              "message": "Cluster list information",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary='Get a list of existing providers'
    )
    def get(self):
        clusters = db.all("clusters")
        return [format_cluster_resp(cluster) for cluster in clusters]

    @swagger.operation(
        notes='Creates a new cluster',
        nickname='postcluster',
        parameters=[
            {
                "name": "name",
                "description": "Name of the cluster (accepts alphanumeric, dash, underscore, and dot characters; min 3 characters)",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "description",
                "description": "Description of the purpose of the cluster.",
                "required": False,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "org_name",
                "description": "Full name of the Organization",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "org_short_name",
                "description": "Short word or abbreviation for the organization",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "city",
                "description": "City for self-signed certificates.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "state",
                "description": "State or province for self-signed certificates.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "country_code",
                "description": "ISO 3166-1 two-character country code for self-signed certificates.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "admin_email",
                "description": "Admin email for the self-signed certifcates.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "ox_cluster_hostname",
                "description": "Hostname to use for the admin interface website.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form",
            },
            {
                "name": "admin_pw",
                "description": "Password for LDAP replication admin.",
                "required": True,
                "allowMultiple": False,
                "dataType": 'string',
                "paramType": "form"
            },
            {
                "name": "weave_ip_network",
                "description": "The IP address for weave network, e.g. 10.20.10.0/24",
                "required": True,
                "dataType": "string",
                "paramType": "form",
            },
        ],
        responseMessages=[
            {
                "code": 201,
                "message": "Created",
            },
            {
                "code": 400,
                "message": "Bad Request",
            },
            {
                "code": 403,
                "message": "Forbidden",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Create a new cluster'
    )
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

        cluster = GluuCluster(fields=data)
        db.persist(cluster, "clusters")

        headers = {
            "Location": url_for("cluster", cluster_id=cluster.id),
        }

        distribute_cluster_data(current_app.config["DATABASE_URI"])
        return format_cluster_resp(cluster), 201, headers
