def test_setup(saml_setup, patched_salt, patched_sleep,
               salt_event_ok):
    # TODO: it might be better to split the tests
    saml_setup.setup()


def test_teardown(saml_setup, patched_salt):
    saml_setup.teardown()
