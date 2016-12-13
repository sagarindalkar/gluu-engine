import pytest


@pytest.mark.parametrize("pubkey_in", [
    "abc",
    "a b c",
    "abc/+=",
    "a+ b/ c=",
])
def test_sanitize_public_key(pubkey_in):
    from gluuengine.reqparser import LicenseKeyReq

    req = LicenseKeyReq()
    data = req.finalize_data({
        "public_key": pubkey_in,
        "public_password": "pub_password",
        "license_password": "license_password",
    })
    assert data["public_key"] != pubkey_in
