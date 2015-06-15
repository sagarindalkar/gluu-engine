def test_setup(oxauth_setup, patched_salt_cmd, patched_sleep):
    # TODO: it might be better to split the tests
    oxauth_setup.setup()
