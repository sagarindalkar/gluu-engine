def test_weave_launch_master(app, db, provider, cluster,
                             patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper
    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.launch_master()


def test_weave_launch_consumer(app, db, provider, cluster,
                               patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper
    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.launch_consumer()


def test_weave_expose_network(app, db, provider, cluster,
                              patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper
    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.expose_network()
