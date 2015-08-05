import pytest


def test_validate_admin_pw():
    from gluuapi.reqparser import ClusterReq
    from marshmallow import ValidationError

    req = ClusterReq()
    with pytest.raises(ValidationError):
        # use password less than 6 chars
        req.validate_admin_pw("abcde")


@pytest.mark.parametrize("name", [
    # whitespace
    "ab a",
    # leading dash
    "-ab",
    # trailing underscore
    "ab_",
    # trailing dash
    "ab-",
    # less than 3 chars
    "ab",
    # leading dot
    ".ab",
    # trailing dot
    "ab.",
])
def test_validate_name_invalid(name):
    from gluuapi.reqparser import ClusterReq
    from marshmallow import ValidationError

    req = ClusterReq()
    with pytest.raises(ValidationError):
        req.validate_name(name)


@pytest.mark.parametrize("name", [
    "abc",
    "a-b_c",
    "a0sd9",
    "GluuClusterTest",
    "gluu.example.com",
    "EXAMPLE",
    "1ab",
    "ab1",
])
def test_validate_name_valid(name):
    from gluuapi.reqparser import ClusterReq

    req = ClusterReq()
    req.validate_name(name)
