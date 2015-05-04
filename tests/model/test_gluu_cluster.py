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
