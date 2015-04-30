def test_setup(monkeypatch, ldap_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_setup_with_replication(monkeypatch, ldap_setup, db):
    from gluuapi.model.ldap_node import ldapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    peer_node = ldapNode()
    ldap_setup.cluster.add_node(peer_node)
    db.persist(peer_node, "nodes")
    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")

    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_after_setup(monkeypatch, ldap_setup):
    from gluuapi.database import db
    from gluuapi.model.oxauth_node import oxauthNode
    from gluuapi.model.oxtrust_node import oxtrustNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    oxauth = oxauthNode()
    oxauth.id = "auth-123"
    ldap_setup.cluster.add_node(oxauth)
    db.persist(oxauth, "nodes")

    oxtrust = oxtrustNode()
    oxtrust.id = "trust-123"
    ldap_setup.cluster.add_node(oxtrust)
    db.persist(oxtrust, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.after_setup()


def test_stop(monkeypatch, ldap_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    ldap_setup.stop()


def test_stop_with_replication(monkeypatch, ldap_setup):
    from gluuapi.database import db
    from gluuapi.model.ldap_node import ldapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    node1 = ldapNode()
    node1.id = "ldap-123"
    db.persist(node1, "nodes")
    ldap_setup.cluster.add_node(node1)

    node2 = ldapNode()
    node2.id = "ldap-456"
    db.persist(node2, "nodes")
    ldap_setup.cluster.add_node(node2)

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.stop()


def test_replicate_from(monkeypatch, ldap_setup, db):
    from gluuapi.model.ldap_node import ldapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    peer_node = ldapNode()
    peer_node.id = "ldap-123"
    db.persist(peer_node, "nodes")
    ldap_setup.cluster.add_node(peer_node)
    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")

    ldap_setup.replicate_from(peer_node)
