import json

import pytest


def test_node_get(app, cluster, db, ldap_node):
    db.persist(ldap_node, "nodes")
    db.persist(cluster, "clusters")

    resp = app.test_client().get("/nodes/{}".format(ldap_node.id))
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert ldap_node.as_dict() == actual_data
    for field in ldap_node.resource_fields.keys():
        assert field in actual_data


def test_node_get_invalid_id(app):
    resp = app.test_client().get("/nodes/random-invalid-id")
    actual_data = json.loads(resp.data)
    assert resp.status_code == 404
    assert "message" in actual_data


def test_node_get_list(app, db, cluster, ldap_node):
    db.persist(ldap_node, "nodes")
    db.persist(cluster, "clusters")

    resp = app.test_client().get("/nodes")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 1

    fields = ldap_node.resource_fields.keys()
    for item in actual_data:
        for field in fields:
            assert field in item


def test_node_get_list_empty(app):
    resp = app.test_client().get("/nodes")
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

    resp = app.test_client().delete("/nodes/{}".format(ldap_node.id))
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

    resp = app.test_client().delete("/nodes/{}".format(httpd_node.id))
    assert resp.status_code == 204


def test_node_delete_failed(app):
    resp = app.test_client().delete("/nodes/random-invalid-id")
    assert resp.status_code == 404


def test_node_delete_in_progress(app, db, ldap_node):
    ldap_node.state = "IN_PROGRESS"
    db.persist(ldap_node, "nodes")
    resp = app.test_client().delete("/nodes/{}".format(ldap_node.name))
    assert resp.status_code == 403


def test_node_post_invalid_connect_delay(app, db, cluster, provider):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/nodes",
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
        "/nodes",
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
        "/nodes",
        data={
            "cluster_id": "123",
            "provider_id": "123",
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 400


def test_node_post_ip_unavailable(monkeypatch, app, db, cluster, provider):
    # fills up reserved IP address using fake values
    monkeypatch.setattr(
        "gluuapi.model.GluuCluster.get_node_addrs",
        lambda cls: ["10.20.10.{}".format(x) for x in xrange(256)]
    )

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/nodes",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "oxauth",
        },
    )
    assert resp.status_code == 403


def test_node_post_invalid_provider(app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().post(
        "/nodes",
        data={
            "cluster_id": cluster.id,
            "provider_id": "123",
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("node_type, helper_class", [
    ("ldap", "LdapModelHelper"),
    ("oxauth", "OxauthModelHelper"),
])
def test_node_post(monkeypatch, app, db, cluster, provider,
                   node_type, helper_class, oxauth_node):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    oxauth_node.state = "SUCCESS"
    db.persist(oxauth_node, "nodes")

    monkeypatch.setattr(
        "gluuapi.helper.{}.setup".format(helper_class),
        lambda cls, connect_delay, exec_delay: None,
    )
    data = {
        "cluster_id": cluster.id,
        "provider_id": provider.id,
        "node_type": node_type,
    }
    if node_type == "httpd":
        data["oxauth_node_id"] = oxauth_node.id

    resp = app.test_client().post("/nodes", data=data)
    assert resp.status_code == 202


def test_node_post_duplicate_oxtrust(monkeypatch, app, db, cluster,
                                     provider, oxtrust_node):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    oxtrust_node.state = "SUCCESS"
    db.persist(oxtrust_node, "nodes")

    monkeypatch.setattr(
        "gluuapi.helper.OxtrustModelHelper.setup",
        lambda cls, connect_delay, exec_delay: None,
    )
    data = {
        "cluster_id": cluster.id,
        "provider_id": provider.id,
        "node_type": "oxtrust",
    }

    resp = app.test_client().post("/nodes", data=data)
    assert resp.status_code == 403


def test_node_post_nonmaster_oxtrust(monkeypatch, app, db, cluster,
                                     provider, license_key):
    db.persist(cluster, "clusters")
    provider.type = "consumer"
    db.persist(provider, "providers")
    license_key.valid = True
    license_key.metadata["expiration_date"] = None
    db.persist(license_key, "license_keys")

    monkeypatch.setattr(
        "gluuapi.helper.OxtrustModelHelper.setup",
        lambda cls, connect_delay, exec_delay: None,
    )
    data = {
        "cluster_id": cluster.id,
        "provider_id": provider.id,
        "node_type": "oxtrust",
    }

    resp = app.test_client().post("/nodes", data=data)
    assert resp.status_code == 403


def test_node_post_expired_license(app, db, provider, cluster, license_key):
    db.persist(cluster, "clusters")
    license_key.valid = False
    db.persist(license_key, "license_keys")
    provider.type = "consumer"
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/nodes",
        data={
            "cluster_id": cluster.id,
            "provider_id": provider.id,
            "node_type": "httpd",
        },
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("force_delete, status_code", [
    (0, 403),
    ("false", 403),
    ("False", 403),
    ("f", 403),
    (1, 204),
    ("true", 204),
    ("True", 204),
    ("t", 204),
])
def test_node_delete_force(monkeypatch, app, db, ldap_node, cluster,
                           provider, force_delete, status_code):
    monkeypatch.setattr(
        "gluuapi.setup.LdapSetup.teardown",
        lambda cls: None,
    )

    monkeypatch.setattr(
        "gluuapi.helper.PrometheusHelper.update",
        lambda cls: None,
    )

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    ldap_node.state = "IN_PROGRESS"
    ldap_node.cluster_id = cluster.id
    ldap_node.provider_id = provider.id
    db.persist(ldap_node, "nodes")

    resp = app.test_client().delete(
        "/nodes/{}?force_rm={}".format(ldap_node.id, force_delete),
    )
    assert resp.status_code == status_code
