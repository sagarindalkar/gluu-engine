def test_cluster_as_dict():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()
    actual = cluster.as_dict()

    for field in cluster.resource_fields.keys():
        assert field in actual


def test_cluster_max_allowed_nodes(cluster):
    assert cluster.max_allowed_ldap_nodes == 4


def test_decrypted_admin_pw():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster({"admin_pw": "secret"})
    assert cluster.decrypted_admin_pw == "secret"


def test_ip_addr_available(cluster):
    # fills up reserved IP address using fake values
    cluster.reserved_ip_addrs = [ip for ip in range(253)]
    assert cluster.ip_addr_available is False

    cluster.reserved_ip_addrs.pop()
    assert cluster.ip_addr_available is True


def test_reserve_ip_addr(cluster):
    assert cluster.reserve_ip_addr() == tuple(["10.20.10.1", 24])


def test_unreserve_ip_addr(cluster):
    assert cluster.unreserve_ip_addr("10.20.10.1") is None


def test_get_node_objects(db, cluster, ldap_node, oxauth_node,
                          oxtrust_node, httpd_node):
    # saves all nodes
    db.persist(ldap_node, "nodes")
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")
    db.persist(httpd_node, "nodes")
    data = cluster.get_node_objects(state=None)

    for item in data:
        assert item.cluster_id == cluster.id
    assert len(data) == 4


def test_get_httpd_objects(db, cluster, httpd_node):
    db.persist(httpd_node, "nodes")
    data = cluster.get_httpd_objects(state=None)

    assert len(data) == 1
    assert data[0].type == httpd_node.type


def test_get_oxtrust_objects(db, cluster, oxtrust_node):
    db.persist(oxtrust_node, "nodes")
    data = cluster.get_oxtrust_objects(state=None)

    assert len(data) == 1
    assert data[0].type == oxtrust_node.type


def test_get_oxauth_objects(db, cluster, oxauth_node):
    db.persist(oxauth_node, "nodes")
    data = cluster.get_oxauth_objects(state=None)

    assert len(data) == 1
    assert data[0].type == oxauth_node.type


def test_get_ldap_objects(db, cluster, ldap_node):
    db.persist(ldap_node, "nodes")
    data = cluster.get_ldap_objects(state=None)

    assert len(data) == 1
    assert data[0].type == ldap_node.type


def test_exposed_weave_ip():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()
    cluster.weave_ip_network = "10.2.1.0/24"

    addr, prefixlen = cluster.exposed_weave_ip
    assert addr == "10.2.1.254"
    assert prefixlen == 24
