def test_setup(ldap_setup, patched_salt_cmd, patched_sleep):
    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_setup_with_replication(ldap_setup, db, cluster, patched_salt_cmd,
                                patched_sleep):
    from gluuapi.model import LdapNode

    peer_node = LdapNode()
    peer_node.cluster_id = cluster.id
    db.persist(peer_node, "nodes")
    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")

    # TODO: it might be better to split the tests
    assert ldap_setup.setup()


def test_after_setup(ldap_setup, patched_salt_cmd):
    from gluuapi.database import db
    from gluuapi.model import OxauthNode
    from gluuapi.model import OxtrustNode

    oxauth = OxauthNode()
    oxauth.id = "auth-123"
    db.persist(oxauth, "nodes")

    oxtrust = OxtrustNode()
    oxtrust.id = "trust-123"
    db.persist(oxtrust, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.after_setup()


def test_teardown(ldap_setup, patched_salt_cmd):
    ldap_setup.teardown()


def test_teardown_with_replication(ldap_setup, cluster, patched_salt_cmd):
    from gluuapi.database import db
    from gluuapi.model import LdapNode

    node1 = LdapNode()
    node1.id = "ldap-123"
    node1.cluster_id = cluster.id
    db.persist(node1, "nodes")

    node2 = LdapNode()
    node2.id = "ldap-456"
    node2.cluster_id = cluster.id
    db.persist(node2, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.teardown()


def test_replicate_from(ldap_setup, db, patched_salt_cmd, patched_sleep):
    from gluuapi.model import LdapNode

    peer_node = LdapNode()
    peer_node.id = "ldap-123"
    db.persist(peer_node, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.replicate_from(peer_node)


def test_render_ox_ldap_props(ldap_setup, db, oxauth_node,
                              oxtrust_node, patched_salt_cmd):
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")
    ldap_setup.render_ox_ldap_props()
