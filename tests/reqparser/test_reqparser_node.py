import pytest


def test_validate_invalid_provider(db):
    from marshmallow import ValidationError
    from gluuengine.reqparser import NodeReq

    req = NodeReq()

    with pytest.raises(ValidationError):
        req.validate_provider("random-provider-id")


def test_validate_invalid_reused_provider(db, generic_provider, master_node):
    from marshmallow import ValidationError
    from gluuengine.reqparser import NodeReq

    master_node.provider_id = generic_provider.id
    db.persist(generic_provider, "providers")
    db.persist(master_node, "nodes")

    req = NodeReq()

    with pytest.raises(ValidationError):
        req.validate_provider(generic_provider.id)


@pytest.mark.parametrize("name", [
    # contains invalid ~ char
    "a~",
])
def test_validate_invalid_regex_name(name):
    from marshmallow import ValidationError
    from gluuengine.reqparser import NodeReq

    req = NodeReq()

    with pytest.raises(ValidationError):
        req.validate_name(name)


def test_validate_reused_name(db, master_node):
    from marshmallow import ValidationError
    from gluuengine.reqparser import NodeReq

    db.persist(master_node, "nodes")

    req = NodeReq()

    with pytest.raises(ValidationError):
        req.validate_name(master_node.name)
