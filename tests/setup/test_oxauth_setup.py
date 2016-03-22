def test_setup(oxauth_setup, ldap_node, cluster, db,
               patched_sleep, patched_exec_cmd, patched_run):
    db.persist(cluster, "clusters")
    ldap_node.state = "SUCCESS"
    db.persist(ldap_node, "nodes")
    # TODO: it might be better to split the tests
    oxauth_setup.setup()


def test_teardown(oxauth_setup, patched_exec_cmd):
    oxauth_setup.teardown()
