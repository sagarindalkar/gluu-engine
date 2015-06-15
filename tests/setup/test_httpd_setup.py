def test_setup(db, httpd_setup, oxauth_node, oxtrust_node, patched_salt_cmd):
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")
    # TODO: it might be better to split the tests
    httpd_setup.setup()


def test_after_setup(db, httpd_setup, oxauth_node, oxtrust_node,
                     provider, patched_salt_cmd):
    db.persist(provider, "providers")
    db.persist(oxauth_node, "nodes")
    db.persist(oxtrust_node, "nodes")
    httpd_setup.provider = provider
    httpd_setup.after_setup()

def test_teardown(db, httpd_setup, oxtrust_node, provider, patched_salt_cmd):
    db.persist(provider, "providers")
    db.persist(oxtrust_node, "nodes")
    httpd_setup.provider = provider
    httpd_setup.teardown()
