import json


def test_node_get(app, cluster, db, ldap_node):
    db.persist(ldap_node, "nodes")
    cluster.add_node(ldap_node)
    db.persist(cluster, "clusters")

    resp = app.test_client().get("/node/{}".format(ldap_node.id))
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert ldap_node.as_dict() == actual_data
    for field in ldap_node.resource_fields.keys():
        assert field in actual_data


def test_node_get_invalid_id(app):
    resp = app.test_client().get("/node/random-invalid-id")
    actual_data = json.loads(resp.data)
    assert resp.status_code == 404
    assert actual_data["code"] == 404
    assert "message" in actual_data


def test_node_get_list(app, db, cluster, ldap_node):
    db.persist(ldap_node, "nodes")
    cluster.add_node(ldap_node)
    db.persist(cluster, "clusters")

    resp = app.test_client().get("/node")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 1

    fields = ldap_node.resource_fields.keys()
    for item in actual_data:
        for field in fields:
            assert field in item


def test_node_get_list_empty(app):
    resp = app.test_client().get("/node")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 0
    assert actual_data == []


def test_node_delete(monkeypatch, app, db, cluster, provider, ldap_node):
    db.persist(provider, "providers")
    ldap_node.provider_id = provider.id
    db.persist(ldap_node, "nodes")
    cluster.add_node(ldap_node)
    db.persist(cluster, "clusters")

    monkeypatch.setattr(
        "gluuapi.setup.ldap_setup.LdapSetup.teardown",
        lambda cls: None,
    )

    monkeypatch.setattr(
        "gluuapi.helper.prometheus_helper.PrometheusHelper.update",
        lambda cls: None,
    )

    resp = app.test_client().delete("/node/{}".format(ldap_node.id))
    assert resp.status_code == 204


def test_node_delete_failed(app):
    resp = app.test_client().delete("/node/random-invalid-id")
    assert resp.status_code == 404


def test_node_post_custom_delay(app, db, cluster, provider):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "httpd",
            "connect_delay": "not-a-number",
            "exec_delay": "not-a-number",
        },
    )
    assert resp.status_code == 400
