def test_setup(oxauth_setup, patched_salt_cmd, patched_sleep,
               ldap_node, cluster, db):
    db.persist(cluster, "clusters")
    ldap_node.state = "SUCCESS"
    db.persist(ldap_node, "nodes")
    # TODO: it might be better to split the tests
    oxauth_setup.setup()


def test_teardown(oxauth_setup):
    oxauth_setup.teardown()
