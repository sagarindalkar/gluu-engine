def test_setup(oxidp_setup, patched_exec_cmd, patched_sleep):
    # TODO: it might be better to split the tests
    oxidp_setup.setup()


def test_teardown(oxidp_setup, patched_exec_cmd):
    oxidp_setup.teardown()
