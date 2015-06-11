def test_perform_job(db, license, oxd_resp_ok, validator_ok):
    import copy
    from gluuapi.task import LicenseExpirationTask
    from gluuapi.utils import timestamp_millis

    # license with expired timestamp
    license.valid = True
    license.metadata["expiration_date"] = timestamp_millis() - (60 * 60 * 24 * 1000)
    db.persist(license, "licenses")

    # license having ``None`` as ``expiration_date`` value
    license2 = copy.copy(license)
    license2.id = "abc"
    license2.metadata["expiration_date"] = None
    db.persist(license2, "licenses")

    let = LicenseExpirationTask()
    let.perform_job()
