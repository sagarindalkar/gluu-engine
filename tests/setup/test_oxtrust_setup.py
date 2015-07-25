def test_setup(oxtrust_setup, patched_salt_cmd, patched_sleep):
    # TODO: it might be better to split the tests
    oxtrust_setup.setup()


def test_delete_httpd_cert(oxtrust_setup, patched_salt_cmd):
    oxtrust_setup.delete_httpd_cert()


def test_teardown(oxtrust_setup, patched_salt_cmd):
    oxtrust_setup.teardown()
