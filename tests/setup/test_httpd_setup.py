def test_setup(monkeypatch, db, httpd_setup, oxauth_node, oxtrust_node):
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    # TODO: it might be better to split the tests
    httpd_setup.setup()


def test_after_setup(monkeypatch, db, httpd_setup,
                     oxauth_node, oxtrust_node, provider):
    db.persist(provider, "providers")
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    httpd_setup.provider = provider
    httpd_setup.after_setup()

def test_teardown(monkeypatch, db, httpd_setup,
                  oxtrust_node, provider):
    db.persist(provider, "providers")
    db.persist(oxtrust_node, "nodes")

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    httpd_setup.provider = provider
    httpd_setup.teardown()
