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
    class Response(object):
        ok = True
        text = ""

        def json(self):
            return {"license": "xyz"}

    # monkeypatch ``requests.post`` directly as we cannot monkeypatch
    # ``requests`` inside ``gluuapi.utils.retrieve_signed_license`` call
    monkeypatch.setattr("requests.post", lambda url, data: Response())

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
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 201


def test_license_list_post_notretrieved(monkeypatch, app):
    class Response(object):
        ok = False
        text = ""

        def json(self):
            return {"license": "xyz"}

    # monkeypatch ``requests.post`` directly as we cannot monkeypatch
    # ``requests`` inside ``gluuapi.utils.retrieve_signed_license`` call
    monkeypatch.setattr("requests.post", lambda url, data: Response())

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


def test_license_put(monkeypatch, app, db, license):
    class Response(object):
        ok = True
        text = ""

        def json(self):
            return {"license": "xyz"}

    db.persist(license, "licenses")

    # monkeypatch ``requests.post`` directly as we cannot monkeypatch
    # ``requests`` inside ``gluuapi.utils.retrieve_signed_license`` call
    monkeypatch.setattr("requests.post", lambda url, data: Response())

    with codecs.open("tests/resource/validator_output.txt", encoding="utf-8") as fp:
        patch_output = fp.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )

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


def test_license_put_notretrieved(monkeypatch, app, db, license):
    class Response(object):
        ok = False
        text = ""

    db.persist(license, "licenses")

    # monkeypatch ``requests.post`` directly as we cannot monkeypatch
    # ``requests`` inside ``gluuapi.utils.retrieve_signed_license`` call
    monkeypatch.setattr("requests.post", lambda url, data: Response())

    with codecs.open("tests/resource/validator_output.txt", encoding="utf-8") as fp:
        patch_output = fp.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )

    resp = app.test_client().put(
        "/license/{}".format(license.id),
        data={
            "public_key": "pubkey",
            "public_password": "pubpasswd",
            "license_password": "licensepasswd",
        },
    )
    assert resp.status_code == 422
