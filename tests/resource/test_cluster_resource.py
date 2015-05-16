import json


def test_cluster_post(monkeypatch, app, db):
    from gluuapi.model import GluuCluster

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    resp = app.test_client().post(
        "/cluster",
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
    for field in GluuCluster.resource_fields.keys():
        assert field in actual_data


def test_cluster_get(app, config, cluster, db):
    db.persist(cluster, "clusters")
    resp = app.test_client().get("/cluster/{}".format(cluster.id))
    assert resp.status_code == 200


def test_cluster_get_invalid_id(app):
    resp = app.test_client().get("/cluster/random-invalid-id")
    actual_data = json.loads(resp.data)
    assert resp.status_code == 404
    assert actual_data["code"] == 404
    assert "message" in actual_data


def test_cluster_get_list(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().get("/cluster")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 1


def test_cluster_get_list_empty(app):
    resp = app.test_client().get("/cluster")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 0
    assert actual_data == []


def test_cluster_delete(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().delete("/cluster/{}".format(cluster.id))
    assert resp.status_code == 204


def test_cluster_delete_failed(app):
    resp = app.test_client().delete("/cluster/random-invalid-id")
    assert resp.status_code == 404


def test_cluster_post_max_cluster_reached(app, db, cluster):
    db.persist(cluster, "clusters")

    resp = app.test_client().post(
        "/cluster",
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
