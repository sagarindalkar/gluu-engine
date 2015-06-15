import pytest


def test_get_random_chars():
    from gluuapi.utils import get_random_chars

    random_chars = get_random_chars()
    assert len(random_chars) == 12


def test_run():
    from gluuapi.utils import run

    result = run("echo gluu")
    assert result.strip() == "gluu"


def test_run_error():
    import subprocess
    from gluuapi.utils import run

    with pytest.raises(SystemExit):
        run("random-command")

    with pytest.raises(subprocess.CalledProcessError):
        run("random-command", exit_on_error=False)


def test_ldap_encode():
    from gluuapi.utils import ldap_encode

    passwd = "secret"
    assert ldap_encode(passwd).startswith("{SSHA}")


def test_get_quad():
    from gluuapi.utils import get_quad

    quad = get_quad()
    assert len(quad) == 4


def test_encrypt_text():
    from gluuapi.utils import encrypt_text

    key = "123456789012345678901234"
    text = "password"
    assert encrypt_text(text, key) == "im6yqa0BROeTNcwvx4XCaw=="


def test_decrypt_text():
    from gluuapi.utils import decrypt_text

    key = "123456789012345678901234"
    enc_text = "im6yqa0BROeTNcwvx4XCaw=="
    assert decrypt_text(enc_text, key) == "password"
