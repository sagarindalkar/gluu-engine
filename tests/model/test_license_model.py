def test_expired_date(license_key):
    from gluuapi.utils import timestamp_millis

    ts = timestamp_millis() - (60 * 60 * 24 * 1000)
    license_key.valid = True
    license_key.metadata["expiration_date"] = ts
    assert license_key.expired is True
