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


def test_validate_hostname_duplicated(db, provider):
    from gluuapi.reqparser import ProviderReq
    from marshmallow import ValidationError

    db.persist(provider, "providers")

    reqparser = ProviderReq()
    with pytest.raises(ValidationError):
        reqparser.validate_hostname(provider.hostname)


def test_validate_hostname_invalid_update(db, provider):
    from gluuapi.reqparser import EditProviderReq
    from marshmallow import ValidationError

    db.persist(provider, "providers")
    reqparser = EditProviderReq(context={"provider": provider})

    with pytest.raises(ValidationError):
        reqparser.validate_hostname("-a")


def test_validate_hostname_duplicated_update(db, provider):
    from gluuapi.reqparser import EditProviderReq
    from gluuapi.model import Provider
    from marshmallow import ValidationError

    # provider that needs to be updated
    db.persist(provider, "providers")

    # existing provider
    provider2 = Provider()
    provider2.hostname = "random"
    db.persist(provider2, "providers")

    reqparser = EditProviderReq(context={"provider": provider})
    with pytest.raises(ValidationError):
        # hostname is taken by provider2
        reqparser.validate_hostname(provider2.hostname)
