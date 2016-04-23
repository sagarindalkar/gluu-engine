def test_cluster_as_dict():
    from gluuapi.model import Cluster

    cluster = Cluster()
    actual = cluster.as_dict()

    for field in cluster.resource_fields.keys():
        assert field in actual


def test_decrypted_admin_pw():
    from gluuapi.model import Cluster

    cluster = Cluster({"admin_pw": "secret"})
    assert cluster.decrypted_admin_pw == "secret"


def test_reserve_ip_addr(cluster):
    assert cluster.reserve_ip_addr() == tuple(["10.20.10.1", 24])


def test_get_containers(db, cluster, ldap_node, oxauth_node,
                        oxtrust_node):
    # saves all nodes
    db.persist(ldap_node, "nodes")
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")
    data = cluster.get_containers(state=None)

    for item in data:
        assert item.cluster_id == cluster.id
    assert len(data) == 3


def test_exposed_weave_ip():
    from gluuapi.model import Cluster

    cluster = Cluster()
    cluster.weave_ip_network = "10.20.10.0/24"

    addr, prefixlen = cluster.exposed_weave_ip
    assert addr == "10.20.10.254"
    assert prefixlen == 24


def test_get_nodes_by_state(db, cluster, ldap_node):
    db.persist(cluster, "clusters")
    ldap_node.state = "FAILED"
    db.persist(ldap_node, "nodes")
    assert cluster.get_containers(type_="ldap", state="FAILED")


def test_prometheus_weave_ip():
    from gluuapi.model import Cluster

    cluster = Cluster()
    cluster.weave_ip_network = "10.20.10.0/24"

    addr, prefixlen = cluster.prometheus_weave_ip
    assert addr == "10.20.10.253"
    assert prefixlen == 24
