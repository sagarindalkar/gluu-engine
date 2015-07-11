import pytest


def test_ip_addr_available(cluster, db):
    from gluuapi.reqparser import NodeReq
    from marshmallow import ValidationError
    from netaddr import IPNetwork

    # set last_fetched_addr to use last IPNetwork.iter_hosts element
    cluster.last_fetched_addr = str(IPNetwork(cluster.weave_ip_network)[-2])
    db.persist(cluster, "clusters")
    with pytest.raises(ValidationError):
        NodeReq().validate_cluster(cluster.id)
