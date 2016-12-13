def test_no_metadata(license_key):
    license_key.metadata = {}
    assert license_key.expired is True


def test_no_expiration_date(license_key):
    license_key.metadata["expiration_date"] = ""
    assert license_key.expired is True


def test_non_expired_license(monkeypatch, license_key):
    import time

    # current date in milliseconds
    now = time.time() * 1000

    class Response(object):
        def json(self):
            return now

    tomorrow = now + (60 * 60 * 24 * 2 * 1000)
    monkeypatch.setattr("requests.get", lambda url: Response())
    license_key.metadata["expiration_date"] = tomorrow
    assert license_key.expired is False


def test_expired_license(monkeypatch, license_key):
    import time

    # current date in milliseconds
    now = time.time() * 1000

    class Response(object):
        def json(self):
            return now

    yesterday = now - (60 * 60 * 24 * 2 * 1000)
    monkeypatch.setattr("requests.get", lambda url: Response())
    license_key.metadata["expiration_date"] = yesterday
    assert license_key.expired is True


def test_decrypted_public_key(license_key):
    from gluuengine.utils import generate_passkey
    from gluuengine.utils import encrypt_text

    passkey = generate_passkey()
    public_key = encrypt_text("pub_key", passkey)

    license_key.passkey = passkey
    license_key.public_key = public_key
    assert license_key.decrypted_public_key == "pub_key"


def test_decrypted_public_password(license_key):
    from gluuengine.utils import generate_passkey
    from gluuengine.utils import encrypt_text

    passkey = generate_passkey()
    public_password = encrypt_text("pub_password", passkey)

    license_key.passkey = passkey
    license_key.public_password = public_password

    assert license_key.decrypted_public_password == "pub_password"


def test_decrypted_license_password(license_key):
    from gluuengine.utils import generate_passkey
    from gluuengine.utils import encrypt_text

    passkey = generate_passkey()
    license_password = encrypt_text("license_password", passkey)

    license_key.passkey = passkey
    license_key.license_password = license_password
    assert license_key.decrypted_license_password == "license_password"


def test_get_and_count_workers(app, db, license_key, worker_node):
    with app.app_context():
        db.persist(worker_node, "nodes")
        assert license_key.get_workers()
        assert license_key.count_workers() >= 1
