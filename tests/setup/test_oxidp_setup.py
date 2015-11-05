def test_setup(oxidp_setup, patched_salt, patched_sleep,
               salt_event_ok):
    # TODO: it might be better to split the tests
    oxidp_setup.setup()


def test_teardown(oxidp_setup, patched_salt):
    oxidp_setup.teardown()
