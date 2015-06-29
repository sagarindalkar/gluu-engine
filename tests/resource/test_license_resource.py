import json


def test_license_list_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/licenses")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


def test_license_list_get_empty(app):
    resp = app.test_client().get("/licenses")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


def test_license_post(app, oxd_resp_ok, validator_ok, license_credential, db):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().post(
        "/licenses",
        data={
            "code": "abc",
            "credential_id": license_credential.id,
        },
    )
    assert resp.status_code == 201


def test_license_post_invalid_params(app):
    resp = app.test_client().post(
        "/licenses",
        data={
            "code": "abc",
            "credential_id": "abc",
        },
    )
    assert resp.status_code == 400


def test_license_post_notretrieved(app, oxd_resp_err, db, license_credential):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().post(
        "/licenses",
        data={
            "code": "abc",
            "credential_id": license_credential.id,
        },
    )
    assert resp.status_code == 422


def test_license_post_invalid_creds(app, db, license_credential, oxd_resp_ok, validator_err):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().post(
        "/licenses",
        data={"code": "abc", "credential_id": license_credential.id},
    )
    assert resp.status_code == 201


def test_license_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/licenses/{}".format(license.id))
    assert resp.status_code == 200

    item = json.loads(resp.data)
    assert item["id"] == license.id


def test_license_get_notfound(app):
    resp = app.test_client().get("/licenses/abc")
    assert resp.status_code == 404


def test_license_delete_notfound(app):
    resp = app.test_client().delete("/licenses/abc")
    assert resp.status_code == 404


def test_license_delete(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().delete("/licenses/{}".format(license.id))
    assert resp.status_code == 204


def test_credential_post(app):
    resp = app.test_client().post(
        "/license_credentials",
        data={
            "name": "test",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


def test_credential_post_invalid_params(app):
    resp = app.test_client().post(
        "/license_credentials",
        data={
            "name": "test",
            "public_key": "pubkey",
        },
    )
    assert resp.status_code == 400


def test_credential_get_list(app, db, license_credential):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().get("/license_credentials")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


def test_credential_get_notfound(app):
    resp = app.test_client().get("/license_credentials/abc")
    assert resp.status_code == 404


def test_credential_get(app, db, license_credential):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().get("/license_credentials/{}".format(license_credential.id))
    assert resp.status_code == 200


def test_credential_put_notfound(app):
    resp = app.test_client().put("/license_credentials/abc")
    assert resp.status_code == 404


def test_credential_put(app, db, license_credential, license, validator_ok):
    db.persist(license_credential, "license_credentials")
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license_credentials/{}".format(license_credential.id),
        data={
            "name": "test",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


def test_credential_put_incorrect_creds(app, db, license_credential, license, validator_err):
    db.persist(license_credential, "license_credentials")
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license_credentials/{}".format(license_credential.id),
        data={
            "name": "test",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


def test_credential_put_invalid_params(app, db, license_credential, license, validator_ok):
    db.persist(license_credential, "license_credentials")
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license_credentials/{}".format(license_credential.id),
        data={
            "name": "test",
            "public_key": "pubkey",
        },
    )
    assert resp.status_code == 400


def test_credential_delete_notfound(app):
    resp = app.test_client().delete("/license_credentials/abc")
    assert resp.status_code == 404


def test_credential_delete(app, db, license_credential):
    db.persist(license_credential, "license_credentials")
    resp = app.test_client().delete("/license_credentials/{}".format(license_credential.id))
    assert resp.status_code == 204
