import json

import pytest


def test_cluster_post(app, db, patched_salt):
    from gluuapi.model import Cluster

    resp = app.test_client().post(
        "/clusters",
        data={
            "name": "test-cluster-1",
            "description": "test cluster",
            "ox_cluster_hostname": "ox.example.com",
            "org_name": "Gluu Federation",
            "org_short_name": "Gluu",
            "country_code": "US",
            "city": "Austin",
            "state": "Texas",
            "admin_email": "john@example.com",
            "admin_pw": "secret",
            "weave_ip_network": "10.20.10.1/24",
        },
    )
    actual_data = json.loads(resp.data)

    assert resp.status_code == 201
    for field in Cluster.resource_fields.keys():
        assert field in actual_data


def test_cluster_get(app, config, cluster, db):
    db.persist(cluster, "clusters")
    resp = app.test_client().get("/clusters/{}".format(cluster.id))
    assert resp.status_code == 200


def test_cluster_get_invalid_id(app):
    resp = app.test_client().get("/clusters/random-invalid-id")
    actual_data = json.loads(resp.data)
    assert resp.status_code == 404
    assert "message" in actual_data


def test_cluster_get_list(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().get("/clusters")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 1


def test_cluster_get_list_empty(app):
    resp = app.test_client().get("/clusters")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 0
    assert actual_data == []


def test_cluster_delete(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().delete("/clusters/{}".format(cluster.id))
    assert resp.status_code == 204


def test_cluster_delete_failed(app):
    resp = app.test_client().delete("/clusters/random-invalid-id")
    assert resp.status_code == 404


def test_cluster_delete_nodes_exist(app, db, cluster, ldap_node):
    db.persist(cluster, "clusters")
    ldap_node.state = "SUCCESS"
    ldap_node.cluster_id = cluster.id
    db.persist(ldap_node, "nodes")
    resp = app.test_client().delete("/clusters/{}".format(cluster.id))
    assert resp.status_code == 403


def test_cluster_post_max_cluster_reached(app, db, cluster):
    db.persist(cluster, "clusters")

    resp = app.test_client().post(
        "/clusters",
        data={
            "name": "test-cluster-1",
            "description": "test cluster",
            "ox_cluster_hostname": "ox.example.com",
            "org_name": "Gluu Federation",
            "org_short_name": "Gluu",
            "country_code": "US",
            "city": "Austin",
            "state": "Texas",
            "admin_email": "john@example.com",
            "admin_pw": "secret",
            "weave_ip_network": "10.20.10.1/24",
        },
    )
    assert resp.status_code == 403


def test_cluster_post_invalid_country_code(app, db, patched_salt):
    resp = app.test_client().post(
        "/clusters",
        data={
            "name": "test-cluster-1",
            "description": "test cluster",
            "ox_cluster_hostname": "ox.example.com",
            "org_name": "Gluu Federation",
            "org_short_name": "Gluu",
            "country_code": "USA",
            "city": "Austin",
            "state": "Texas",
            "admin_email": "john@example.com",
            "admin_pw": "secret",
            "weave_ip_network": "10.20.10.1/24",
        },
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("weave_ip_network", [
    "abc",
    "10.20.10.0",
    "500.1.2.3/256",
])
def test_cluster_post_invalid_weave_network(app, db, patched_salt, weave_ip_network):
    resp = app.test_client().post(
        "/clusters",
        data={
            "name": "test-cluster-1",
            "description": "test cluster",
            "ox_cluster_hostname": "ox.example.com",
            "org_name": "Gluu Federation",
            "org_short_name": "Gluu",
            "country_code": "US",
            "city": "Austin",
            "state": "Texas",
            "admin_email": "john@example.com",
            "admin_pw": "secret",
            "weave_ip_network": weave_ip_network,
        },
    )
    assert resp.status_code == 400
