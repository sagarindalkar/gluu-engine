import json

import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_post_multiple(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().post(
        "/license_keys",
        data={"name": "test"},
    )
    assert resp.status_code == 403


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_post_invalid_params(app, db):
    resp = app.test_client().post(
        "/license_keys",
        data={
            "name": "test",
            "code": "abc",
            "public_key": "pubkey",
        },
    )
    assert resp.status_code == 400


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_post(app):
    resp = app.test_client().post(
        "/license_keys",
        data={
            "name": "test",
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_get_list(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().get("/license_keys")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_get_notfound(app):
    resp = app.test_client().get("/license_keys/abc")
    assert resp.status_code == 404


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_get(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().get("/license_keys/{}".format(license_key.id))
    assert resp.status_code == 200


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_put_notfound(app):
    resp = app.test_client().put("/license_keys/abc")
    assert resp.status_code == 404


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_put(app, db, license_key, validator_ok):
    db.persist(license_key, "license_keys")
    resp = app.test_client().put(
        "/license_keys/{}".format(license_key.id),
        data={
            "name": "test",
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_put_enable_nodes(app, db, license_key, validator_ok,
                                      oxauth_node, provider,
                                      patched_salt, salt_event_ok):
    provider.type = "consumer"
    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    oxauth_node.state = "DISABLED"
    db.persist(oxauth_node, "nodes")
    db.persist(license_key, "license_keys")
    resp = app.test_client().put(
        "/license_keys/{}".format(license_key.id),
        data={
            "name": "test",
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_put_incorrect_creds(app, db, license_key, validator_err):
    db.persist(license_key, "license_keys")
    resp = app.test_client().put(
        "/license_keys/{}".format(license_key.id),
        data={
            "name": "test",
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_put_invalid_params(app, db, license_key, validator_ok):
    db.persist(license_key, "license_keys")
    resp = app.test_client().put(
        "/license_keys/{}".format(license_key.id),
        data={
            "name": "test",
            "public_key": "pubkey",
            "code": "abc",
        },
    )
    assert resp.status_code == 400


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_delete_notfound(app):
    resp = app.test_client().delete("/license_keys/abc")
    assert resp.status_code == 404


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_delete_provider_exist(app, db, provider, license_key):
    provider.type = "consumer"
    db.persist(provider, "providers")
    db.persist(license_key, "license_keys")
    resp = app.test_client().delete("/license_keys/{}".format(license_key.id))
    assert resp.status_code == 403


@pytest.mark.skip(reason="rewrite needed")
def test_license_key_delete(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().delete("/license_keys/{}".format(license_key.id))
    assert resp.status_code == 204
