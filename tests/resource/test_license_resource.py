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


def test_license_list_post(app):
    resp = app.test_client().post(
        "/license",
        data={
            "code": "abc",
            "name": "license1",
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
