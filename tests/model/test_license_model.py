def test_expired_date(license):
    from gluuapi.utils import timestamp_millis

    ts = timestamp_millis() - (60 * 60 * 24 * 1000)
    license.valid = True
    license.metadata["expiration_date"] = ts
    assert license.expired is True
