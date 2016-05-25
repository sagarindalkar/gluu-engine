import pytest


@pytest.mark.parametrize("pubkey_in, pubkey_out", [
    ("abc", "abc"),
    ("a b c", "a+b+c"),
    ("abc/+=", "abc/+="),
    ("a+ b/ c=", "a++b/+c="),
])
def test_sanitize_public_key(pubkey_in, pubkey_out):
    from gluuengine.reqparser import LicenseKeyReq

    req = LicenseKeyReq().load({
        "public_key": pubkey_in,
    })
    assert req.data == {"public_key": pubkey_out}
