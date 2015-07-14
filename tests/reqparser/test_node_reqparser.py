import pytest
from marshmallow import ValidationError


def test_ip_addr_available(cluster, db):
    from gluuapi.reqparser import NodeReq
    from netaddr import IPNetwork

    # set last_fetched_addr to use last IPNetwork.iter_hosts element
    cluster.last_fetched_addr = str(IPNetwork(cluster.weave_ip_network)[-2])
    db.persist(cluster, "clusters")
    with pytest.raises(ValidationError):
        NodeReq().validate_cluster(cluster.id)


def test_validate_oxauth_reused(db, httpd_node):
    from gluuapi.reqparser import NodeReq

    db.persist(httpd_node, "nodes")
    ctx = {"node_type": "httpd"}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxauth(httpd_node.oxauth_node_id)


def test_validate_oxauth_invalid_provider(db, oxauth_node, provider):
    from gluuapi.reqparser import NodeReq

    db.persist(provider, "providers")
    oxauth_node.provider_id = "xyz"
    db.persist(oxauth_node, "nodes")

    ctx = {"node_type": "httpd", "provider": provider}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxauth(oxauth_node.id)


def test_validate_oxauth_invalid_state(db, oxauth_node, provider):
    from gluuapi.reqparser import NodeReq

    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    db.persist(oxauth_node, "nodes")

    ctx = {"node_type": "httpd", "provider": provider}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxauth(oxauth_node.id)


def test_validate_oxauth_notfound():
    from gluuapi.reqparser import NodeReq

    ctx = {"node_type": "httpd"}
    node_req = NodeReq(context=ctx)
    with pytest.raises(ValidationError):
        node_req.validate_oxauth("abc")


def test_validate_oxtrust_reused(db, httpd_node):
    from gluuapi.reqparser import NodeReq

    db.persist(httpd_node, "nodes")
    ctx = {"node_type": "httpd"}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxtrust(httpd_node.oxtrust_node_id)


def test_validate_oxtrust_invalid_provider(db, oxtrust_node, provider):
    from gluuapi.reqparser import NodeReq

    db.persist(provider, "providers")
    oxtrust_node.provider_id = "xyz"
    db.persist(oxtrust_node, "nodes")

    ctx = {"node_type": "httpd", "provider": provider}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxtrust(oxtrust_node.id)


def test_validate_oxtrust_invalid_state(db, oxtrust_node, provider):
    from gluuapi.reqparser import NodeReq

    db.persist(provider, "providers")
    oxtrust_node.provider_id = provider.id
    db.persist(oxtrust_node, "nodes")

    ctx = {"node_type": "httpd", "provider": provider}
    node_req = NodeReq(context=ctx)

    with pytest.raises(ValidationError):
        node_req.validate_oxtrust(oxtrust_node.id)


def test_validate_oxtrust_notfound():
    from gluuapi.reqparser import NodeReq

    ctx = {"node_type": "httpd"}
    node_req = NodeReq(context=ctx)
    with pytest.raises(ValidationError):
        node_req.validate_oxtrust("abc")
