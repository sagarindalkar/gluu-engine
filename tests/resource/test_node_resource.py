import json

import pytest


def test_node_get(app, cluster, db, ldap_node):
    db.persist(ldap_node, "nodes")
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


def test_node_delete_ldap(monkeypatch, app, db, cluster, provider, ldap_node):
    db.persist(provider, "providers")
    ldap_node.provider_id = provider.id
    db.persist(ldap_node, "nodes")
    db.persist(cluster, "clusters")

    monkeypatch.setattr(
        "gluuapi.setup.LdapSetup.teardown",
        lambda cls: None,
    )

    monkeypatch.setattr(
        "gluuapi.helper.PrometheusHelper.update",
        lambda cls: None,
    )

    resp = app.test_client().delete("/node/{}".format(ldap_node.id))
    assert resp.status_code == 204


def test_node_delete_httpd(monkeypatch, app, db, cluster,
                           provider, httpd_node):
    db.persist(provider, "providers")
    httpd_node.provider_id = provider.id
    db.persist(httpd_node, "nodes")
    db.persist(cluster, "clusters")

    monkeypatch.setattr(
        "gluuapi.setup.HttpdSetup.teardown",
        lambda cls: None,
    )

    monkeypatch.setattr(
        "gluuapi.helper.PrometheusHelper.update",
        lambda cls: None,
    )

    resp = app.test_client().delete("/node/{}".format(httpd_node.id))
    assert resp.status_code == 204


def test_node_delete_failed(app):
    resp = app.test_client().delete("/node/random-invalid-id")
    assert resp.status_code == 404


def test_node_post_invalid_connect_delay(app, db, cluster, provider):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "httpd",
            "connect_delay": "not-a-number",
        },
    )
    assert resp.status_code == 400


def test_node_post_invalid_exec_delay(app, db, cluster, provider):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "httpd",
            "exec_delay": "not-a-number",
        },
    )
    assert resp.status_code == 400


def test_node_post_invalid_cluster(app, db):
    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": "123",
            "provider_id": "123",
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 400


def test_node_post_ip_unavailable(app, db, cluster):
    # fills up reserved IP address using fake values
    cluster.reserved_ip_addrs = [ip for ip in range(253)]
    db.persist(cluster, "clusters")

    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": "123",
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 403


def test_node_post_invalid_provider(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": "123",
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 400


def test_node_post_max_ldap(app, db, cluster, provider):
    from gluuapi.model import LdapNode

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    for _ in range(cluster.max_allowed_ldap_nodes):
        node = LdapNode()
        node.cluster_id = cluster.id
        db.persist(node, "nodes")

    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "ldap",
        },
    )
    assert resp.status_code == 403


@pytest.mark.parametrize("node_type, helper_class", [
    ("ldap", "LdapModelHelper"),
    ("oxauth", "OxauthModelHelper"),
    ("oxtrust", "OxtrustModelHelper"),
    ("httpd", "HttpdModelHelper"),
])
def test_node_post(monkeypatch, app, db, cluster, provider,
                   node_type, helper_class):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    monkeypatch.setattr(
        "gluuapi.helper.{}.setup".format(helper_class),
        lambda cls, connect_delay, exec_delay: None,
    )
    resp = app.test_client().post(
        "/node",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": node_type,
        },
    )
    assert resp.status_code == 202
