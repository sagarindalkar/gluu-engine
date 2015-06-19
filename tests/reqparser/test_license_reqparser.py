import pytest


@pytest.mark.parametrize("key,safe_key", [
    ("abc def", "abc+def"),
    ("abc+def", "abc+def"),
    ("abc+def/hij", "abc+def/hij"),
    ("abc+def/hij==", "abc+def/hij=="),
])
def test_public_key(key, safe_key):
    from gluuapi.reqparser.license import public_key
    assert public_key(key, "") == safe_key
