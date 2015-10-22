def test_perform_job_renewal(db, license_key, provider,
                             oxd_resp_ok, validator_ok, app):
    from gluuapi.task import LicenseExpirationTask
    from gluuapi.utils import timestamp_millis

    # license with expired timestamp
    license_key.valid = True
    license_key.metadata["expiration_date"] = timestamp_millis() - (60 * 60 * 24 * 1000)
    db.persist(license_key, "license_keys")

    # provider that will be affected by expired license
    db.persist(provider, "providers")

    let = LicenseExpirationTask(app)
    let.perform_job()


def test_perform_job_disable_nodes(db, license_key, provider, oxauth_node,
                                   oxd_resp_err, patched_salt_cmd, app):
    from gluuapi.task import LicenseExpirationTask
    from gluuapi.utils import timestamp_millis

    # license with expired timestamp
    license_key.valid = True
    license_key.metadata["expiration_date"] = timestamp_millis() - (60 * 60 * 24 * 1000)
    db.persist(license_key, "license_keys")

    # provider that will be affected by expired license
    provider.license_key_id = license_key.id
    db.persist(provider, "providers")

    # oxAuth nodes that will be disabled
    db.persist(oxauth_node, "nodes")

    let = LicenseExpirationTask(app)
    let.perform_job()
