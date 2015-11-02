def test_setup(ldap_setup, patched_salt, patched_sleep,
               salt_event_ok):
    # TODO: it might be better to split the tests
    ldap_setup.setup()


def test_setup_with_replication(ldap_setup, db, cluster, patched_salt,
                                patched_sleep, salt_event_ok):
    from gluuapi.model import LdapNode
    from gluuapi.model import STATE_SUCCESS

    peer_node = LdapNode()
    peer_node.cluster_id = cluster.id
    peer_node.state = STATE_SUCCESS
    db.persist(peer_node, "nodes")
    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")

    # TODO: it might be better to split the tests
    assert ldap_setup.setup()


def test_after_setup(cluster, ldap_setup, patched_salt,
                     salt_event_ok, patched_sleep):
    from gluuapi.database import db
    from gluuapi.model import OxauthNode
    from gluuapi.model import OxtrustNode
    from gluuapi.model import STATE_SUCCESS

    db.persist(cluster, "clusters")

    oxauth = OxauthNode()
    oxauth.id = "auth-123"
    oxauth.cluster_id = cluster.id
    oxauth.state = STATE_SUCCESS
    db.persist(oxauth, "nodes")

    oxtrust = OxtrustNode()
    oxtrust.id = "trust-123"
    oxauth.cluster_id = cluster.id
    oxtrust.state = STATE_SUCCESS
    db.persist(oxtrust, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.after_setup()


def test_teardown(ldap_setup, patched_salt, cluster, oxauth_node, db,
                  patched_sleep):
    db.persist(cluster, "clusters")
    oxauth_node.state = "SUCCESS"
    db.persist(oxauth_node, "nodes")
    ldap_setup.teardown()


def test_teardown_with_replication(ldap_setup, cluster,
                                   patched_salt, patched_sleep):
    from gluuapi.database import db
    from gluuapi.model import LdapNode
    from gluuapi.model import STATE_SUCCESS

    node1 = LdapNode()
    node1.id = "ldap-123"
    node1.cluster_id = cluster.id
    node1.state = STATE_SUCCESS
    db.persist(node1, "nodes")

    node2 = LdapNode()
    node2.id = "ldap-456"
    node2.cluster_id = cluster.id
    node2.state = STATE_SUCCESS
    db.persist(node2, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.teardown()


def test_replicate_from(ldap_setup, db, patched_salt, patched_sleep,
                        salt_event_ok):
    from gluuapi.model import LdapNode
    from gluuapi.model import STATE_SUCCESS

    peer_node = LdapNode()
    peer_node.id = "ldap-123"
    peer_node.state = STATE_SUCCESS
    db.persist(peer_node, "nodes")

    db.update(ldap_setup.cluster.id, ldap_setup.cluster, "clusters")
    ldap_setup.replicate_from(peer_node)


def test_notify_ox(ldap_setup, db, oxauth_node,
                   oxtrust_node, patched_salt):
    from gluuapi.model import STATE_SUCCESS

    oxauth_node.state = STATE_SUCCESS
    db.persist(oxauth_node, "nodes")
    oxtrust_node.state = STATE_SUCCESS
    db.persist(oxtrust_node, "nodes")
    ldap_setup.notify_ox()


def test_start_opendj(ldap_setup, patched_salt, salt_event_ok):
    ldap_setup.start_opendj()
