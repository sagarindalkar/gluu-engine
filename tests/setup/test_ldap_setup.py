def test_setup(monkeypatch, ldap_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_setup_with_replication(monkeypatch, ldap_setup, db):
    from gluuapi.model import LdapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    peer_node = LdapNode()
    db.persist(peer_node, "nodes")
    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")

    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_after_setup(monkeypatch, ldap_setup):
    from gluuapi.database import db
    from gluuapi.model import OxauthNode
    from gluuapi.model import OxtrustNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    oxauth = OxauthNode()
    oxauth.id = "auth-123"
    db.persist(oxauth, "nodes")

    oxtrust = OxtrustNode()
    oxtrust.id = "trust-123"
    db.persist(oxtrust, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.after_setup()


def test_stop(monkeypatch, ldap_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    ldap_setup.teardown()


def test_stop_with_replication(monkeypatch, ldap_setup):
    from gluuapi.database import db
    from gluuapi.model import LdapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    node1 = LdapNode()
    node1.id = "ldap-123"
    db.persist(node1, "nodes")

    node2 = LdapNode()
    node2.id = "ldap-456"
    db.persist(node2, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.teardown()


def test_replicate_from(monkeypatch, ldap_setup, db):
    from gluuapi.model import LdapNode

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    peer_node = LdapNode()
    peer_node.id = "ldap-123"
    db.persist(peer_node, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.replicate_from(peer_node)
