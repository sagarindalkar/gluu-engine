def test_setup(oxtrust_setup, patched_exec_cmd, patched_sleep):
    # TODO: it might be better to split the tests
    oxtrust_setup.setup()


def test_delete_web_cert(oxtrust_setup, patched_exec_cmd):
    oxtrust_setup.delete_nginx_cert()


def test_teardown(oxtrust_setup, patched_exec_cmd):
    oxtrust_setup.teardown()
