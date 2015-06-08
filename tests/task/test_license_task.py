def test_get_expired_licenses(db, license):
    import copy
    from gluuapi.task import LicenseExpirationTask

    # license with expired timestamp
    db.persist(license, "licenses")

    # license having ``None`` as ``expiration_date`` value
    license2 = copy.copy(license)
    license2.id = "abc"
    license2.metadata["expiration_date"] = None
    db.persist(license2, "licenses")

    let = LicenseExpirationTask()
    let._get_expired_licenses()


def test_get_providers(db, provider, license):
    from gluuapi.task import LicenseExpirationTask

    db.persist(license, "licenses")
    provider.license_id = license.id
    db.persist(provider, "providers")

    let = LicenseExpirationTask()
    let._get_providers(license)


def test_get_nodes(db, provider, oxauth_node, patched_salt_cmd):
    from gluuapi.task import LicenseExpirationTask

    db.persist(provider, "providers")
    db.persist(oxauth_node, "nodes")

    let = LicenseExpirationTask()
    let._get_nodes(provider)
