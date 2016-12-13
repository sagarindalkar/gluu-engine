import pytest


def test_validate_invalid_node_id(app, db):
    from marshmallow import ValidationError
    from gluuengine.reqparser import ContainerReq

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node("random-node-id")


def test_validate_invalid_node_type(app, db, discovery_node):
    from marshmallow import ValidationError
    from gluuengine.reqparser import ContainerReq

    db.persist(discovery_node, "nodes")

    req = ContainerReq()

    with pytest.raises(ValidationError):
        req.validate_node(discovery_node.id)


def test_validate_node_missing_license(app, db, worker_node):
    from marshmallow import ValidationError
    from gluuengine.reqparser import ContainerReq

    db.persist(worker_node, "nodes")

    req = ContainerReq(context={"enable_license": True})

    with pytest.raises(ValidationError):
        req.validate_node(worker_node.id)


def test_validate_node_expired_license(app, db, worker_node, license_key):
    from marshmallow import ValidationError
    from gluuengine.reqparser import ContainerReq

    db.persist(worker_node, "nodes")
    db.persist(license_key, "license_keys")

    req = ContainerReq(context={"enable_license": True})

    with pytest.raises(ValidationError):
        req.validate_node(worker_node.id)


def test_finalize_data():
    from gluuengine.reqparser import ContainerReq

    req = ContainerReq()
    final_data = req.finalize_data({})
    assert "context" in final_data
