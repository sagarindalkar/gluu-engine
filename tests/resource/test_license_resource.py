import codecs
import json

import pytest


@pytest.fixture
def oxd_resp_ok(monkeypatch):
    class Response(object):
        ok = True
        text = ""

        def json(self):
            return {"license": "xyz"}
    monkeypatch.setattr("requests.post", lambda url, data: Response())


@pytest.fixture
def oxd_resp_err(monkeypatch):
    class Response(object):
        ok = False
        text = ""

        def json(self):
            return {"license": None}
    monkeypatch.setattr("requests.post", lambda url, data: Response())


@pytest.fixture
def validator_ok(monkeypatch):
    with codecs.open("tests/resource/validator_ok.txt", encoding="utf-8") as f:
        patch_output = f.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )


@pytest.fixture
def validator_err(monkeypatch):
    with codecs.open("tests/resource/validator_err.txt", encoding="utf-8") as f:
        patch_output = f.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )


@pytest.fixture
def validator_invalid(monkeypatch):
    monkeypatch.setattr(
        "gluuapi.utils.decode_signed_license",
        lambda sl, pk, pp, lp: {"valid": False, "metadata": None},
    )


def test_license_list_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/license")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


def test_license_list_get_empty(app):
    resp = app.test_client().get("/license")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


def test_license_post(app, oxd_resp_ok, validator_ok):
    resp = app.test_client().post(
        "/license",
        data={
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


def test_license_post_invalid_creds(app, oxd_resp_ok, validator_err):
    resp = app.test_client().post(
        "/license",
        data={
            "code": "abc",
            "public_key": "pubkey a",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


def test_license_post_notretrieved(app, oxd_resp_err):
    resp = app.test_client().post(
        "/license",
        data={
            "code": "abc",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 422


def test_license_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/license/{}".format(license.id))
    assert resp.status_code == 200

    item = json.loads(resp.data)
    assert item["id"] == license.id


def test_license_get_notfound(app):
    resp = app.test_client().get("/license/abc")
    assert resp.status_code == 404


def test_license_put(app, db, license, validator_ok):
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license/{}".format(license.id),
        data={
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 200


def test_license_put_notfound(app):
    resp = app.test_client().put(
        "/license/abc",
        data={
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 404


def test_license_put_invalid_creds(app, db, license, validator_err):
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license/{}".format(license.id),
        data={
            "public_key": "pubkey a",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 422


def test_license_put_invalid_license(app, db, license, validator_invalid):
    db.persist(license, "licenses")
    resp = app.test_client().put(
        "/license/{}".format(license.id),
        data={
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 422


def test_license_delete_notfound(app):
    resp = app.test_client().delete("/license/abc")
    assert resp.status_code == 404


def test_license_delete(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().delete("/license/{}".format(license.id))
    assert resp.status_code == 204
