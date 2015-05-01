import pytest


@pytest.mark.parametrize("hostname", [
    'abc',
    'A0c',
    'A-0c',
    'o12345670123456701234567012345670123456701234567012345670123456',
    '',
    'a',
    '0--0',
])
def test_hostname_type(hostname):
    from gluuapi.reqparser.provider import hostname_type
    assert hostname_type(hostname, "hostname") == hostname


@pytest.mark.parametrize("hostname", [
    '01010',
    'A0c-',
    '-A0c',
    'o123456701234567012345670123456701234567012345670123456701234567',
])
def test_hostname_type_error(hostname):
    from gluuapi.reqparser.provider import hostname_type
    with pytest.raises(ValueError):
        hostname_type(hostname, "hostname")
