def test_weave_launch_master(provider, cluster, patched_salt_cmd):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, "127.0.0.1")
    weave.launch_master()


def test_weave_launch_consumer(provider, cluster, patched_salt_cmd):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, "127.0.0.1")
    weave.launch_consumer()


def test_weave_expose_network(provider, cluster, patched_salt_cmd):
    from gluuapi.helper import WeaveHelper
    weave = WeaveHelper(provider, cluster, "127.0.0.1")
    weave.expose_network()
