import pytest


def test_validate_invalid_node_id(db):
    from marshmallow import ValidationError
    from gluuapi.reqparser import ContainerReq

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node("random-node-id")


def test_validate_invalid_node_type(db, discovery_node):
    from marshmallow import ValidationError
    from gluuapi.reqparser import ContainerReq

    db.persist(discovery_node, "nodes")

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node(discovery_node.id)


def test_validate_node_missing_license(db, worker_node):
    from marshmallow import ValidationError
    from gluuapi.reqparser import ContainerReq

    db.persist(worker_node, "nodes")

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node(worker_node.id)


def test_validate_node_expired_license(db, worker_node, license_key):
    from marshmallow import ValidationError
    from gluuapi.reqparser import ContainerReq

    db.persist(worker_node, "nodes")
    license_key.metadata = {}
    db.persist(license_key, "license_keys")

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node(worker_node.id)


def test_finalize_data():
    from gluuapi.reqparser import ContainerReq

    req = ContainerReq()
    final_data = req.finalize_data({})
    assert "params" in final_data
    assert "context" in final_data
