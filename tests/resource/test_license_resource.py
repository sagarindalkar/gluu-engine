import json


def test_license_key_post_multiple(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().post(
        "/license_keys",
        data={"name": "test"},
    )
    assert resp.status_code == 403


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


def test_license_key_get_list(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().get("/license_keys")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


def test_license_key_get_notfound(app):
    resp = app.test_client().get("/license_keys/abc")
    assert resp.status_code == 404


def test_license_key_get(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().get("/license_keys/{}".format(license_key.id))
    assert resp.status_code == 200


def test_license_key_put_notfound(app):
    resp = app.test_client().put("/license_keys/abc")
    assert resp.status_code == 404


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


def test_license_key_delete_notfound(app):
    resp = app.test_client().delete("/license_keys/abc")
    assert resp.status_code == 404


def test_license_key_delete(app, db, license_key):
    db.persist(license_key, "license_keys")
    resp = app.test_client().delete("/license_keys/{}".format(license_key.id))
    assert resp.status_code == 204
