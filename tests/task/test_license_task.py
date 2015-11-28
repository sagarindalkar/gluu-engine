def test_license_not_expired(
        db, license_key, provider, app,
        oxd_resp_ok, validator_ok):
    from gluuapi.task import LicenseExpirationTask

    license_key.valid = True
    license_key.metadata["expiration_date"] = None
    db.persist(license_key, "license_keys")

    with app.test_request_context():
        let = LicenseExpirationTask(app)
        let.monitor_license()


def test_disable_nodes(db, license_key, provider,
                       oxauth_node, oxidp_node, app,
                       oxd_resp_err, patched_salt,
                       salt_event_ok, patched_sleep):
    from gluuapi.task import LicenseExpirationTask

    # license with expired timestamp
    license_key.valid = False
    db.persist(license_key, "license_keys")

    # provider that will be affected by expired license
    provider.license_key_id = license_key.id
    provider.type = "consumer"
    db.persist(provider, "providers")

    # oxAuth nodes that will be disabled
    oxauth_node.provider_id = provider.id
    oxauth_node.state = "SUCCESS"
    db.persist(oxauth_node, "nodes")

    # oxidp nodes that will be enabled
    oxidp_node.provider_id = provider.id
    oxidp_node.state = "SUCCESS"
    db.persist(oxidp_node, "nodes")

    with app.test_request_context():
        let = LicenseExpirationTask(app)
        let.monitor_license()
        assert db.get(oxauth_node.id, "nodes").state == "DISABLED"


def test_enable_nodes(db, license_key, provider, app,
                      oxauth_node, oxidp_node,
                      oxd_resp_ok, validator_ok,
                      patched_salt, salt_event_ok,
                      patched_sleep):
    from gluuapi.task import LicenseExpirationTask

    # license with expired timestamp
    license_key.valid = False
    db.persist(license_key, "license_keys")

    # provider that will be affected by expired license
    provider.license_key_id = license_key.id
    provider.type = "consumer"
    db.persist(provider, "providers")

    # oxauth nodes that will be enabled
    oxauth_node.provider_id = provider.id
    oxauth_node.state = "DISABLED"
    db.persist(oxauth_node, "nodes")

    # oxidp nodes that will be enabled
    oxidp_node.provider_id = provider.id
    oxidp_node.state = "DISABLED"
    db.persist(oxidp_node, "nodes")

    with app.test_request_context():
        let = LicenseExpirationTask(app)
        let.monitor_license()
        assert db.get(oxauth_node.id, "nodes").state == "SUCCESS"
