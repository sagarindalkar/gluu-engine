import pytest


def test_get_random_chars():
    from gluuengine.utils import get_random_chars

    random_chars = get_random_chars()
    assert len(random_chars) == 12


def test_po_run():
    from gluuengine.utils import po_run

    stdout, stderr, err_code = po_run("echo gluu")
    assert stdout == "gluu"
    assert stderr == ""
    assert err_code == 0


def test_po_run_error():
    from gluuengine.utils import po_run

    with pytest.raises(RuntimeError):
        po_run("random-command")


def test_ldap_encode():
    from gluuengine.utils import ldap_encode

    passwd = "secret"
    assert ldap_encode(passwd).startswith("{SSHA}")


def test_get_quad():
    from gluuengine.utils import get_quad

    quad = get_quad()
    assert len(quad) == 4


def test_encrypt_text():
    from gluuengine.utils import encrypt_text

    key = "123456789012345678901234"
    text = "password"
    assert encrypt_text(text, key) == "im6yqa0BROeTNcwvx4XCaw=="


def test_decrypt_text():
    from gluuengine.utils import decrypt_text

    key = "123456789012345678901234"
    enc_text = "im6yqa0BROeTNcwvx4XCaw=="
    assert decrypt_text(enc_text, key) == "password"
