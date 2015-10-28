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


@pytest.mark.parametrize("base_url", [
    "abc",
    "http://1.1.1.1:2375",  # plain http is forbidden
    "https://abc",  # uses https, but port is missing
    "unixabc",  # prefixed with unix but the path is incorrect
    "httpsabc",  # prefixed with https but the path is incorrect
])
def test_validate_docker_base_url(base_url):
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq()
    with pytest.raises(ValidationError):
        reqparser.validate_docker_base_url(base_url)


def test_validate_ssl_cert():
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq(context={"docker_base_url": "https://0.0.0.0:2375"})
    with pytest.raises(ValidationError):
        reqparser.validate_ssl_cert("")


def test_validate_ssl_key():
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq(context={"docker_base_url": "https://0.0.0.0:2375"})
    with pytest.raises(ValidationError):
        reqparser.validate_ssl_key("")


def test_validate_ca_cert():
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq(context={"docker_base_url": "https://0.0.0.0:2375"})
    with pytest.raises(ValidationError):
        reqparser.validate_ca_cert("")


def test_finalize_data(app):
    from gluuapi.reqparser import ProviderReq

    reqparser = ProviderReq()
    with app.test_request_context():
        data = reqparser.finalize_data({
            "docker_base_url": "https://localhost:2375",
            "hostname": "local",
            "ssl_cert": """-----BEGIN CERTIFICATE-----\n
kye8qHB5Sm43E/PJL+oAPU0OSYe3H7f9pJMwvx0 T7Sa4T8FKl10W76Rn==\n
-----END CERTIFICATE-----\n""",
            "ssl_key": """-----BEGIN RSA PRIVATE KEY-----
kye8qHB5Sm43E/PJL+oAPU0OSYe3H7f9pJMwvx0 T7Sa4T8FKl10W76Rn==
-----END RSA PRIVATE KEY-----""",
            "ca_cert": """-----BEGIN CERTIFICATE-----
kye8qHB5Sm43E/PJL+oAPU0OSYe3H7f9pJMwvx0 T7Sa4T8FKl10W76Rn==
-----END CERTIFICATE-----""",
        })

        assert data["ssl_cert"] == """-----BEGIN CERTIFICATE-----\n
kye8qHB5Sm43E/PJL+oAPU0OSYe3H7f9pJMwvx0+T7Sa4T8FKl10W76Rn==\n
-----END CERTIFICATE-----\n"""
