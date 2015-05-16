def test_provider_list_post(app):
    resp = app.test_client().post(
        "/provider",
        data={
            "docker_base_url": "unix:///var/run/docker.sock",
            "hostname": "local",
        },
    )
    assert resp.status_code == 201


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
