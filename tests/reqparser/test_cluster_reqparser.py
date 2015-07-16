import pytest


def test_validate_admin_pw():
    from gluuapi.reqparser import ClusterReq
    from marshmallow import ValidationError

    req = ClusterReq()
    with pytest.raises(ValidationError):
        # use password less than 6 chars
        req.validate_admin_pw("abcde")
