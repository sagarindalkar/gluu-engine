import json
import os
import shutil

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

    os.unlink(os.path.join(
        app.config["LOG_DIR"],
        "{}-teardown.log".format(ldap_node.name),
    ))
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
            "provider_id": provider.id,
            "node_type": "ldap",
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
            "provider_id": provider.id,
            "node_type": "ldap",
            "exec_delay": "not-a-number",
        },
    )
    assert resp.status_code == 400


def test_node_post_invalid_cluster(app, db):
    resp = app.test_client().post(
        "/nodes",
        data={
            "provider_id": "123",
            "node_type": "ldap",
        },
    )
    assert resp.status_code == 400


def test_node_post_ip_unavailable(monkeypatch, app, db, cluster, provider):
    # fills up reserved IP address using fake values
    monkeypatch.setattr(
        "gluuapi.model.Cluster.get_container_addrs",
        lambda cls: ["10.20.10.{}".format(x) for x in xrange(256)]
    )

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/nodes",
        data={
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
            "provider_id": "123",
            "node_type": "ldap",
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
        "provider_id": provider.id,
        "node_type": node_type,
    }
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
            "provider_id": provider.id,
            "node_type": "ldap",
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

    try:
        os.unlink(os.path.join(
            app.config["LOG_DIR"],
            "{}-teardown.log".format(ldap_node.name),
        ))
    except OSError:
        pass
    assert resp.status_code == status_code


def test_node_duplicated_nginx(app, db, cluster, provider, nginx_node):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    nginx_node.state = "SUCCESS"
    nginx_node.cluster_id = cluster.id
    nginx_node.provider_id = provider.id
    db.persist(nginx_node, "nodes")

    resp = app.test_client().post(
        "/nodes",
        data={
            "provider_id": provider.id,
            "node_type": "nginx",
        },
    )
    assert resp.status_code == 403


def test_node_ldap_max_exceeded(app, db, cluster, provider, ldap_node):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    for i in range(4):
        ldap_node.state = "SUCCESS"
        ldap_node.cluster_id = cluster.id
        ldap_node.provider_id = provider.id
        db.persist(ldap_node, "nodes")

    resp = app.test_client().post(
        "/nodes",
        data={
            "provider_id": provider.id,
            "node_type": "ldap",
        },
    )
    assert resp.status_code == 403


def test_list_node_log(app, db, node_log):
    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs")
    assert resp.status_code == 200


def test_get_node_log(app, db, node_log):
    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs/{}".format(node_log.id))
    assert resp.status_code == 200


def test_get_node_log_not_found(app):
    resp = app.test_client().get("/node_logs/random")
    assert resp.status_code == 404


def test_get_node_setup_log(app, db, node_log):
    dummy_log_src = os.path.join(os.path.dirname(__file__), "setup.log")
    dummy_log_dest = os.path.join(app.config["LOG_DIR"], node_log.setup_log)
    shutil.copyfile(dummy_log_src, dummy_log_dest)

    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs/{}/setup".format(node_log.id))

    try:
        os.unlink(dummy_log_dest)
    except OSError:
        pass
    assert resp.status_code == 200


def test_get_node_setup_log_invalid_node(app, node_log):
    resp = app.test_client().get("/node_logs/{}/setup".format(node_log.id))
    assert resp.status_code == 404


def test_get_node_teardown_log_not_found(app, db, node_log):
    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs/{}/teardown".format(node_log.id))
    assert resp.status_code == 404


def test_get_node_teardown_log(app, db, node_log):
    dummy_log_src = os.path.join(os.path.dirname(__file__), "teardown.log")
    dummy_log_dest = os.path.join(app.config["LOG_DIR"], node_log.teardown_log)
    shutil.copyfile(dummy_log_src, dummy_log_dest)

    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs/{}/teardown".format(node_log.id))

    try:
        os.unlink(dummy_log_dest)
    except OSError:
        pass
    assert resp.status_code == 200


def test_get_node_teardown_log_invalid_node(app, node_log):
    resp = app.test_client().get("/node_logs/{}/teardown".format(node_log.id))
    assert resp.status_code == 404


def test_get_node_setup_log_not_found(app, db, node_log):
    db.persist(node_log, "node_logs")

    resp = app.test_client().get("/node_logs/{}/setup".format(node_log.id))
    assert resp.status_code == 404


def test_delete_node_log(app, db, node_log):
    db.persist(node_log, "node_logs")

    resp = app.test_client().delete("/node_logs/{}".format(node_log.id))
    assert resp.status_code == 204


def test_delete_node_log_not_found(app):
    resp = app.test_client().delete("/node_logs/random")
    assert resp.status_code == 404
