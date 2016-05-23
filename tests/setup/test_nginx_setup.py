import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_setup(nginx_setup, patched_sleep, patched_exec_cmd, patched_run):
    # TODO: it might be better to split the tests
    nginx_setup.setup()


@pytest.mark.skip(reason="rewrite needed")
def test_setup_restart_nginx(nginx_setup, patched_exec_cmd):
    nginx_setup.restart_nginx()


@pytest.mark.skip(reason="rewrite needed")
def test_after_setup(nginx_setup, nginx_node, provider,
                     patched_salt, patched_run):
    from gluuapi.model import STATE_SUCCESS

    nginx_node.state = STATE_SUCCESS
    nginx_setup.node = nginx_node
    provider.type = "master"
    nginx_setup.provider = provider
    nginx_setup.after_setup()


@pytest.mark.skip(reason="rewrite needed")
def test_teardown(nginx_setup, nginx_node, provider):
    from gluuapi.model import STATE_SUCCESS

    nginx_node.state = STATE_SUCCESS
    nginx_setup.node = nginx_node
    provider.type = "master"
    nginx_setup.provider = provider
    nginx_setup.teardown()
