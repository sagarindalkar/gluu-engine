import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_setup(oxidp_setup, patched_exec_cmd, patched_sleep, patched_run):
    # TODO: it might be better to split the tests
    oxidp_setup.setup()


@pytest.mark.skip(reason="rewrite needed")
def test_teardown(oxidp_setup, patched_exec_cmd):
    oxidp_setup.teardown()
