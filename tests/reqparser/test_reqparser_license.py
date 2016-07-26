import pytest


@pytest.mark.parametrize("pubkey_in, pubkey_out", [
    ("abc", "abc"),
    ("a b c", "a+b+c"),
    ("abc/+=", "abc/+="),
    ("a+ b/ c=", "a++b/+c="),
])
def test_sanitize_public_key(pubkey_in, pubkey_out):
    from gluuengine.reqparser import LicenseKeyReq

    req = LicenseKeyReq()
    data = req.urlsafe_public_key({"public_key": pubkey_in})
    assert data["public_key"] == pubkey_out
