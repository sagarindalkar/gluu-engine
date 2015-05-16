import pytest


def test_country_code():
    from gluuapi.reqparser.cluster import country_code
    assert country_code("US", "countryCode") == "US"


def test_invalid_country_code():
    from gluuapi.reqparser.cluster import country_code

    with pytest.raises(ValueError):
        result = country_code("USA", "countryCode")
        assert "countryCode" in result


def test_admin_email():
    from gluuapi.reqparser.cluster import admin_email
    assert admin_email("support@example.com", "admin_email") == "support@example.com"


@pytest.mark.parametrize("email", [
    "random",
    "random@example",
    "random@",
])
def test_invalid_admin_email(email):
    from gluuapi.reqparser.cluster import admin_email

    with pytest.raises(ValueError):
        result = admin_email(email, "admin_email")
        assert "admin_email" in result


def test_weave_network_type():
    from gluuapi.reqparser.cluster import weave_network_type
    assert weave_network_type("10.20.10.1/24", "weave_ip_network") == "10.20.10.1/24"


def test_invalid_weave_network_type():
    from gluuapi.reqparser.cluster import weave_network_type
    with pytest.raises(ValueError):
        weave_network_type("abc", "weave_ip_network")
