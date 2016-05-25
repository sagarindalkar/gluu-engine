import pytest


@pytest.mark.parametrize("addr", [
    "10.10.10.10",
    "gluu.example.com",
])
def test_validate_generic_ip_address(addr):
    from gluuengine.reqparser import GenericProviderReq

    req = GenericProviderReq()
    assert req.validate_generic_ip_address(addr) is None


@pytest.mark.parametrize("addr", [
    "-a",
])
def test_validate_invalid_generic_ip_address(addr):
    from gluuengine.reqparser import GenericProviderReq
    from marshmallow import ValidationError

    req = GenericProviderReq()
    with pytest.raises(ValidationError):
        req.validate_generic_ip_address(addr)


@pytest.mark.parametrize("name", [
    # contains dash char
    "example-provider",
])
def test_validate_invalid_name(name):
    from marshmallow import ValidationError
    from gluuengine.reqparser import GenericProviderReq

    req = GenericProviderReq()

    with pytest.raises(ValidationError):
        req.validate_name(name)


def test_validate_invalid_generic_ssh_key():
    from marshmallow import ValidationError
    from gluuengine.reqparser import GenericProviderReq

    req = GenericProviderReq()

    with pytest.raises(ValidationError):
        req.validate_generic_ssh_key("/random/path/to/ssh/key")


@pytest.mark.parametrize("user", [
    "a" * 32,
    "-john",
])
def test_validate_invalid_generic_ssh_user(user):
    from marshmallow import ValidationError
    from gluuengine.reqparser import GenericProviderReq

    req = GenericProviderReq()

    with pytest.raises(ValidationError):
        req.validate_generic_ssh_user(user)


@pytest.mark.parametrize("port", [
    1023,
    49153,
])
def test_validate_invalid_generic_ssh_port(port):
    from marshmallow import ValidationError
    from gluuengine.reqparser import GenericProviderReq

    req = GenericProviderReq()

    with pytest.raises(ValidationError):
        req.validate_generic_ssh_port(port)
