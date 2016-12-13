def test_get_containers(app, db, master_node, ldap_container):
    ldap_container.node_id = master_node.id
    db.persist(ldap_container, "containers")
    data = master_node.get_containers(state=None)

    for item in data:
        assert item.node_id == master_node.id


def test_get_containers_by_state(app, db, master_node, ldap_container):
    ldap_container.node_id = master_node.id
    ldap_container.state = "FAILED"
    db.persist(ldap_container, "containers")
    assert master_node.get_containers(type_="ldap", state="FAILED")


def test_count_containers(app, db, worker_node, ldap_container):
    ldap_container.node_id = worker_node.id
    db.persist(ldap_container, "containers")
    assert worker_node.count_containers(state=None) == 1


def test_count_containers_by_state(app, db, worker_node, ldap_container):
    ldap_container.node_id = worker_node.id
    ldap_container.state = "FAILED"
    db.persist(ldap_container, "containers")
    assert worker_node.count_containers(type_="ldap", state="FAILED") == 1


def test_enforced_node_name(discovery_node):
    assert discovery_node.name == "discovery-node"
