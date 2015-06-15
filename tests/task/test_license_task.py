def test_perform_job_renewal(db, license, license_credential, provider,
                             oxd_resp_ok, validator_ok):
    from gluuapi.task import LicenseExpirationTask
    from gluuapi.utils import timestamp_millis

    # license with expired timestamp
    license.valid = True
    license.metadata["expiration_date"] = timestamp_millis() - (60 * 60 * 24 * 1000)
    db.persist(license, "licenses")
    db.persist(license_credential, "license_credentials")

    # provider that will be affected by expired license
    provider.license_id = license.id
    db.persist(provider, "providers")

    let = LicenseExpirationTask()
    let.perform_job()


def test_perform_job_disable_nodes(db, license, license_credential,
                                   provider, oxauth_node,
                                   oxd_resp_err, patched_salt_cmd):
    from gluuapi.task import LicenseExpirationTask
    from gluuapi.utils import timestamp_millis

    # license with expired timestamp
    license.valid = True
    license.metadata["expiration_date"] = timestamp_millis() - (60 * 60 * 24 * 1000)
    db.persist(license, "licenses")
    db.persist(license_credential, "license_credentials")

    # provider that will be affected by expired license
    provider.license_id = license.id
    db.persist(provider, "providers")

    # oxAuth nodes that will be disabled
    db.persist(oxauth_node, "nodes")

    let = LicenseExpirationTask()
    let.perform_job()
