import pytest


@pytest.mark.parametrize("hostname", [
    'abc',
    'A0c',
    'A-0c',
    'o12345670123456701234567012345670123456701234567012345670123456',
    '',
    'a',
    '0--0',
    'ip-172-31-24-54.ec2.internal',
])
def test_validate_hostname_valid(hostname):
    from gluuapi.reqparser import ProviderReq

    reqparser = ProviderReq()
    assert reqparser.validate_hostname(hostname) is None


@pytest.mark.parametrize("hostname", [
    "-a",
])
def test_validate_hostname_invalid(hostname):
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq()
    with pytest.raises(ValidationError):
        reqparser.validate_hostname(hostname)
