import pytest


class _DummyNode(object):
    """Acts as a fake Node until we have a stable Node model.
    """
    def __init__(self, id_, type_):
        self.id = id_
        self.type = type_

    def as_dict(self):
        return self.__dict__


def test_cluster_add_ldap_node(cluster, ldap_node):
    cluster.add_node(ldap_node)
    assert getattr(cluster, "ldap_nodes")[0] == ldap_node.id


def test_cluster_add_oxauth_node(cluster, oxauth_node):
    cluster.add_node(oxauth_node)
    assert getattr(cluster, "oxauth_nodes")[0] == oxauth_node.id


def test_cluster_add_oxtrust_node(cluster, oxtrust_node):
    cluster.add_node(oxtrust_node)
    assert getattr(cluster, "oxtrust_nodes")[0] == oxtrust_node.id


def test_cluster_add_unsupported_node():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()

    # ensure adding unsupported node raises error
    with pytest.raises(ValueError):
        node = _DummyNode(id_="123", type_="random")
        cluster.add_node(node)


def test_cluster_as_dict():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()
    actual = cluster.as_dict()

    for field in cluster.resource_fields.keys():
        assert field in actual


def test_cluster_remove_ldap_node(cluster, ldap_node):
    cluster.add_node(ldap_node)
    cluster.remove_node(ldap_node)
    assert getattr(cluster, "ldap_nodes") == []


def test_cluster_remove_oxauth_node(cluster, oxauth_node):
    cluster.add_node(oxauth_node)
    cluster.remove_node(oxauth_node)
    assert getattr(cluster, "oxauth_nodes") == []


def test_cluster_remove_oxtrust_node(cluster, oxtrust_node):
    cluster.add_node(oxtrust_node)
    cluster.remove_node(oxtrust_node)
    assert getattr(cluster, "oxtrust_nodes") == []


def test_cluster_remove_unsupported_node():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()

    # ensure removing unsupported node raises error
    with pytest.raises(ValueError):
        node = _DummyNode(id_="123", type_="random")
        cluster.remove_node(node)


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

    # adds nodes into cluster
    cluster.add_node(ldap_node)
    cluster.add_node(oxauth_node)
    cluster.add_node(oxtrust_node)
    cluster.add_node(httpd_node)

    # saves cluster
    db.persist(cluster, "clusters")

    data = cluster.get_node_objects()

    for item in data:
        assert item.cluster_id == cluster.id
    assert len(data) == 4


def test_get_httpd_objects(db, cluster, httpd_node):
    db.persist(httpd_node, "nodes")
    cluster.add_node(httpd_node)
    db.persist(cluster, "clusters")
    data = cluster.get_httpd_objects()

    assert len(data) == 1
    assert data[0].type == httpd_node.type


def test_get_oxtrust_objects(db, cluster, oxtrust_node):
    db.persist(oxtrust_node, "nodes")
    cluster.add_node(oxtrust_node)
    db.persist(cluster, "clusters")
    data = cluster.get_oxtrust_objects()

    assert len(data) == 1
    assert data[0].type == oxtrust_node.type


def test_get_oxauth_objects(db, cluster, oxauth_node):
    db.persist(oxauth_node, "nodes")
    cluster.add_node(oxauth_node)
    db.persist(cluster, "clusters")
    data = cluster.get_oxauth_objects()

    assert len(data) == 1
    assert data[0].type == oxauth_node.type


def test_get_ldap_objects(db, cluster, ldap_node):
    db.persist(ldap_node, "nodes")
    cluster.add_node(ldap_node)
    db.persist(cluster, "clusters")
    data = cluster.get_ldap_objects()

    assert len(data) == 1
    assert data[0].type == ldap_node.type
