import json


def test_provider_no_cluster(app):
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "master",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_master(monkeypatch, app, db, cluster,
                                   patched_salt, patched_sleep):
    monkeypatch.setattr(
        "gluuapi.helper.WeaveHelper.launch",
        lambda cls: None,
    )
    db.persist(cluster, "clusters")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "master",
        },
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["type"] == "master"


def test_provider_list_post_duplicated_master(app, db, provider, cluster):
    db.persist(cluster, "clusters")
    provider.type = "master"
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "master",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_license_key_notfound(app, db, provider, cluster):
    db.persist(cluster, "clusters")
    # creates a master first
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 400


def test_provider_list_post_consumer_no_master(monkeypatch, app, db, cluster):
    db.persist(cluster, "clusters")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "consumer",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_consumer_no_license(app, db, cluster, provider):
    db.persist(cluster, "clusters")
    # create master provider first
    provider.type = "master"
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "consumer",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_consumer_unretrieved_license(
        app, db, cluster, license_key, oxd_resp_err, provider):
    db.persist(cluster, "clusters")
    # create master provider first
    provider.type = "master"
    db.persist(provider, "providers")
    db.persist(license_key, "license_keys")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "consumer",
        },
    )
    assert resp.status_code == 422


def test_provider_list_post_consumer(monkeypatch, app, db, cluster,
                                     patched_salt, patched_sleep,
                                     license_key, oxd_resp_ok,
                                     validator_ok, provider):
    db.persist(cluster, "clusters")
    # create master provider first
    provider.type = "master"
    db.persist(provider, "providers")
    db.persist(license_key, "license_keys")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "consumer",
        },
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["type"] == "consumer"


def test_provider_list_post_consumer_no_meta(
        monkeypatch, app, db, cluster, patched_salt, patched_sleep,
        license_key, oxd_resp_ok, validator_err, provider):
    db.persist(cluster, "clusters")
    # create master provider first
    provider.type = "master"
    db.persist(provider, "providers")
    db.persist(license_key, "license_keys")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "type": "consumer",
        },
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["type"] == "consumer"


def test_provider_list_get(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().get("/providers")
    assert resp.status_code == 200


def test_provider_get(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().get("/providers/{}".format(provider.id))
    assert resp.status_code == 200


def test_provider_get_not_found(app):
    resp = app.test_client().get("/providers/random-id")
    assert resp.status_code == 404


def test_provider_delete(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().delete("/providers/{}".format(provider.id))
    assert resp.status_code == 204


def test_provider_delete_not_found(app):
    resp = app.test_client().delete("/providers/random-id")
    assert resp.status_code == 404


def test_provider_delete_having_nodes(app, db, provider, ldap_node):
    db.persist(ldap_node, "nodes")
    db.persist(provider, "providers")
    resp = app.test_client().delete("/providers/{}".format(provider.id))
    assert resp.status_code == 403


def test_provider_put_notfound(app):
    resp = app.test_client().put(
        "/providers/abc",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "abc",
        },
    )
    assert resp.status_code == 404


def test_provider_put_missing_params(app, db, provider):
    provider.license_id = "abc"
    db.persist(provider, "providers")

    resp = app.test_client().put(
        "/providers/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
        },
    )
    assert resp.status_code == 400


def test_provider_put_updated(app, db, provider, oxauth_node,
                              patched_salt, license_key,
                              validator_ok, cluster, patched_sleep):
    from gluuapi.model import STATE_DISABLED

    db.persist(cluster, "clusters")
    license_key.metadata = {"expiration_date": None}
    license_key.valid = True
    db.persist(license_key, "license_keys")
    provider.license_key_id = license_key.id
    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    oxauth_node.state = STATE_DISABLED
    db.persist(oxauth_node, "nodes")

    resp = app.test_client().put(
        "/providers/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "localhost",
        },
    )
    assert resp.status_code == 200
