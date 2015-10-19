def test_weave_launch_master(app, provider, cluster,
                             patched_salt_cmd, patched_sleep):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, app)
    weave.launch_master()


def test_weave_launch_consumer(app, provider, cluster,
                               patched_salt_cmd, patched_sleep):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, app)
    weave.launch_consumer()


def test_weave_expose_network(app, provider, cluster,
                              patched_salt_cmd, patched_sleep):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, app)
    weave.expose_network()
