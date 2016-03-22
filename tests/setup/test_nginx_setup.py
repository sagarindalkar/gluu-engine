def test_setup(nginx_setup, patched_sleep, patched_exec_cmd, patched_run):
    # TODO: it might be better to split the tests
    nginx_setup.setup()


def test_setup_restart_nginx(nginx_setup, patched_exec_cmd):
    nginx_setup.restart_nginx()


def test_setup_notify_oxtrust(nginx_setup, oxtrust_node, provider, db,
                              patched_sleep, patched_exec_cmd):
    from gluuapi.model import STATE_SUCCESS

    oxtrust_node.provider_id = provider.id
    oxtrust_node.state = STATE_SUCCESS
    db.persist(oxtrust_node, "nodes")
    db.persist(provider, "providers")

    nginx_setup.provider = provider
    nginx_setup.notify_oxtrust()


def test_setup_notify_oxtrust_skipped(nginx_setup):
    nginx_setup.notify_oxtrust()


def test_after_setup(nginx_setup, nginx_node, provider,
                     patched_salt, patched_run):
    from gluuapi.model import STATE_SUCCESS

    nginx_node.state = STATE_SUCCESS
    nginx_setup.node = nginx_node
    provider.type = "master"
    nginx_setup.provider = provider
    nginx_setup.after_setup()


def test_teardown(nginx_setup, nginx_node, provider):
    from gluuapi.model import STATE_SUCCESS

    nginx_node.state = STATE_SUCCESS
    nginx_setup.node = nginx_node
    provider.type = "master"
    nginx_setup.provider = provider
    nginx_setup.teardown()
