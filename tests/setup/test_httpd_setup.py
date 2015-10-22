def test_setup(db, httpd_setup, oxauth_node, oxtrust_node, patched_salt_cmd,
               patched_salt_cmd_async, salt_event_ok):
    from gluuapi.model import STATE_SUCCESS

    oxauth_node.state = STATE_SUCCESS
    db.persist(oxauth_node, "nodes")
    oxtrust_node.state = STATE_SUCCESS
    db.persist(oxtrust_node, "nodes")
    # TODO: it might be better to split the tests
    httpd_setup.setup()


def test_after_setup(db, httpd_setup, oxauth_node, oxtrust_node,
                     provider, patched_salt_cmd, patched_sleep,
                     patched_salt_cmd_async, salt_event_ok):
    from gluuapi.model import STATE_SUCCESS

    db.persist(provider, "providers")
    oxauth_node.state = STATE_SUCCESS
    db.persist(oxauth_node, "nodes")
    oxtrust_node.state = STATE_SUCCESS
    db.persist(oxtrust_node, "nodes")
    httpd_setup.provider = provider
    httpd_setup.after_setup()

def test_teardown(db, httpd_setup, oxtrust_node, provider,
                  patched_salt_cmd, patched_sleep,
                  patched_salt_cmd_async, salt_event_ok):
    from gluuapi.model import STATE_SUCCESS

    db.persist(provider, "providers")
    oxtrust_node.state = STATE_SUCCESS
    db.persist(oxtrust_node, "nodes")
    httpd_setup.provider = provider
    httpd_setup.teardown()


def test_remove_pidfile(httpd_setup, patched_salt_cmd,
                        patched_salt_cmd_async, salt_event_ok):
    httpd_setup.remove_pidfile()
