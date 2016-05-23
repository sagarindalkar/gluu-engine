import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_setup(oxtrust_setup, patched_exec_cmd, patched_sleep, patched_run):
    # TODO: it might be better to split the tests
    oxtrust_setup.setup()


@pytest.mark.skip(reason="rewrite needed")
def test_teardown(oxtrust_setup, patched_exec_cmd):
    oxtrust_setup.teardown()
