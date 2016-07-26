def test_no_metadata(license_key):
    license_key.metadata = {}
    assert license_key.expired is True


def test_expired_date(license_key):
    from gluuengine.utils import timestamp_millis

    ts = timestamp_millis() - (60 * 60 * 24 * 1000)
    license_key.metadata["expiration_date"] = ts
    assert license_key.expired is True


def test_non_expired_date(license_key):
    license_key.metadata["expiration_date"] = None
    assert license_key.expired is False


def test_decrypted_public_key(license_key):
    assert license_key.decrypted_public_key == "pub_key"


def test_decrypted_public_password(license_key):
    assert license_key.decrypted_public_password == "pub_password"


def test_decrypted_license_password(license_key):
    assert license_key.decrypted_license_password == "license_password"


def test_get_workers(app, db, license_key, worker_node):
    with app.app_context():
        db.persist(worker_node, "nodes")
        assert license_key.get_workers()


def test_count_workers(app, db, license_key, worker_node):
    with app.app_context():
        db.persist(worker_node, "nodes")
        assert license_key.count_workers() >= 1
