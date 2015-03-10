import pytest


def test_get_random_chars():
    from api.helper.common_helper import get_random_chars

    random_chars = get_random_chars()
    assert len(random_chars) == 12


def test_run():
    from api.helper.common_helper import run

    result = run("echo gluu")
    assert result.strip() == "gluu"


def test_run_error():
    import subprocess
    from api.helper.common_helper import run

    with pytest.raises(SystemExit):
        run("random-command")

    with pytest.raises(subprocess.CalledProcessError):
        run("random-command", exit_on_error=False)


def test_encrypt_password():
    from api.helper.common_helper import encrypt_password

    passwd = "secret"
    assert encrypt_password(passwd).startswith("{SSHA}")