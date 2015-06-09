import json


def test_provider_list_post_master(app):
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 201
    assert json.loads(resp.data)["type"] == "master"


def test_provider_list_post_duplicated_master(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_consumer_duplicated(app, db, license, provider):
    db.persist(license, "licenses")

    # creates a master first
    db.persist(provider, "providers")

    # set as consumer
    provider.license_id = license.id
    db.persist(provider, "providers")

    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_license_notfound(app, db, provider):
    # creates a master first
    db.persist(provider, "providers")
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "abc",
        },
    )
    assert resp.status_code == 400


def test_provider_list_post_invalid_license(monkeypatch, app, db, license, provider):
    db.persist(provider, "providers")

    # makes the license as invalid
    license.valid = False
    db.persist(license, "licenses")
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_expired_license(monkeypatch, app, db, license, provider):
    # creates a master first
    db.persist(provider, "providers")
    db.persist(license, "licenses")
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_list_post_consumer_no_master(monkeypatch, app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_list_get(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().get("/provider")
    assert resp.status_code == 200


def test_provider_get(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().get("/provider/{}".format(provider.id))
    assert resp.status_code == 200


def test_provider_get_not_found(app):
    resp = app.test_client().get("/provider/random-id")
    assert resp.status_code == 404


def test_provider_delete(app, db, provider):
    db.persist(provider, "providers")
    resp = app.test_client().delete("/provider/{}".format(provider.id))
    assert resp.status_code == 204


def test_provider_delete_not_found(app):
    resp = app.test_client().delete("/provider/random-id")
    assert resp.status_code == 404


def test_provider_delete_having_nodes(app, db, provider, ldap_node):
    db.persist(ldap_node, "nodes")
    db.persist(provider, "providers")
    resp = app.test_client().delete("/provider/{}".format(provider.id))
    assert resp.status_code == 403


def test_provider_put_notfound(app):
    resp = app.test_client().put(
        "/provider/abc",
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
        "/provider/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "",
        },
    )
    assert resp.status_code == 400


def test_provider_put_license_reused(app, db, license, provider):
    import copy

    db.persist(license, "licenses")

    # creates a master first
    db.persist(provider, "providers")

    # set a consumer
    provider2 = copy.deepcopy(provider)
    provider2.id = "abc"
    provider2.license_id = license.id
    db.persist(provider2, "providers")

    # set another consumer
    provider3 = copy.deepcopy(provider)
    provider3.id = "def"
    provider3.license_id = "abc"
    db.persist(provider3, "providers")

    resp = app.test_client().put(
        "/provider/{}".format(provider3.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_put_license_notfound(app, db, provider, license):
    db.persist(license, "licenses")
    provider.license_id = license.id
    db.persist(provider, "providers")

    resp = app.test_client().put(
        "/provider/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": "abc",
        },
    )
    assert resp.status_code == 400


def test_provider_put_invalid_license(app, db, license, provider):
    license.valid = False
    db.persist(license, "licenses")
    provider.license_id = license.id
    db.persist(provider, "providers")

    # makes the license as invalid
    license.valid = False
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/provider/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_put_expired_license(app, db, license, provider):

    license.metadata["expiration_date"] -= 1000
    db.persist(license, "licenses")
    provider.license_id = license
    db.persist(provider, "providers")

    resp = app.test_client().put(
        "/provider/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 403


def test_provider_put_updated(app, db, license, provider,
                              oxauth_node, patched_salt_cmd):
    license.metadata["expiration_date"] += 1000
    db.persist(license, "licenses")
    provider.license_id = license
    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    db.persist(oxauth_node, "nodes")

    resp = app.test_client().put(
        "/provider/{}".format(provider.id),
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "localhost",
            "license_id": license.id,
        },
    )
    assert resp.status_code == 200
