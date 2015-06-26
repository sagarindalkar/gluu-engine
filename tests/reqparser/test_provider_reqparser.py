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


def test_validate_docker_config():
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    reqparser = ProviderReq()
    with pytest.raises(ValidationError):
        data = {
            "docker_base_url": "https://localhost:2375",
            "ssl_cert": "",
            "ssl_key": "",
            "ca_cert": "",
        }
        reqparser.validate_docker_config(data)


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
