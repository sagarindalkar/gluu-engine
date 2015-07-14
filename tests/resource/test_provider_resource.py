import json


def test_provider_no_cluster(app):
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_master(monkeypatch, app, db, cluster, patched_salt_cmd):
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
        },
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["type"] == "master"


def test_provider_list_post_duplicated_master(app, db, provider, cluster):
    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_consumer_duplicated(app, db, license,
                                                provider, cluster):
    db.persist(cluster, "clusters")
    db.persist(license, "licenses")

    # creates a master first
    db.persist(provider, "providers")

    # set as consumer
    provider.license_id = license.id
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 400


def test_provider_list_post_license_notfound(app, db, provider, cluster):
    db.persist(cluster, "clusters")
    # creates a master first
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "abc",
        },
    )
    assert resp.status_code == 400


def test_provider_list_post_expired_license(monkeypatch, app, db,
                                            license, provider, cluster):
    db.persist(cluster, "clusters")
    # creates a master first
    db.persist(provider, "providers")
    db.persist(license, "licenses")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 400


def test_provider_list_post_consumer_no_master(monkeypatch, app, db,
                                               license, cluster):
    db.persist(cluster, "clusters")
    license.valid = True
    license.metadata["expiration_date"] = None
    db.persist(license, "licenses")
    resp = app.test_client().post(
        "/providers",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


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
            "hostname": "local",
            "license_id": "",
        },
    )
    assert resp.status_code == 400


def test_provider_put_license_reused(app, db, license, provider):
    import copy

    license.valid = True
    license.metadata["expiration_date"] = None
    db.persist(license, "licenses")

    # set a consumer
    provider1 = copy.deepcopy(provider)
    provider1.id = "abc"
    provider1.license_id = license.id
    db.persist(provider1, "providers")

    # set another consumer
    provider2 = copy.deepcopy(provider1)
    provider2.id = "def"
    provider2.license_id = "abc"
    db.persist(provider2, "providers")

    resp = app.test_client().put(
        "/providers/{}".format(provider2.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 400


def test_provider_put_license_notfound(app, db, provider, license):
    db.persist(license, "licenses")
    provider.license_id = license.id
    db.persist(provider, "providers")

    resp = app.test_client().put(
        "/providers/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "abc",
        },
    )
    assert resp.status_code == 400


def test_provider_put_expired_license(app, db, license, provider, validator_err):

    db.persist(license, "licenses")
    provider.license_id = license
    db.persist(provider, "providers")

    resp = app.test_client().put(
        "/providers/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 400


def test_provider_put_updated(app, db, license, provider,
                              oxauth_node, patched_salt_cmd,
                              license_key, validator_ok, cluster):
    from gluuapi.model import STATE_DISABLED

    db.persist(cluster, "clusters")
    db.persist(license_key, "license_keys")
    license.license_key_id = license_key.id
    license.metadata = {"expiration_date": None}
    license.valid = True
    db.persist(license, "licenses")
    provider.license_id = license
    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    oxauth_node.state = STATE_DISABLED
    db.persist(oxauth_node, "nodes")

    resp = app.test_client().put(
        "/providers/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "localhost",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 200
