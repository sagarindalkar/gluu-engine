import codecs
import json


def test_license_list_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/license")
    assert resp.status_code == 200
    assert json.loads(resp.data) != []


def test_license_list_get_empty(app):
    resp = app.test_client().get("/license")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


def test_license_list_post(monkeypatch, app):
    with codecs.open("tests/resource/validator_output.txt", encoding="utf-8") as fp:
        patch_output = fp.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )

    resp = app.test_client().post(
        "/license",
        data={
            "code": "abc",
            "billing_email": "admin@example.com",
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


def test_license_get(app, db, license):
    db.persist(license, "licenses")
    resp = app.test_client().get("/license/{}".format(license.id))
    assert resp.status_code == 200

    item = json.loads(resp.data)
    assert item["id"] == license.id


def test_license_get_notfound(app):
    resp = app.test_client().get("/license/abc")
    assert resp.status_code == 404
