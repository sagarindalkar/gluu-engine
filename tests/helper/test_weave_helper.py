import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_weave_launch_master(app, db, provider, cluster,
                             patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper

    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.launch_master()


@pytest.mark.skip(reason="rewrite needed")
def test_weave_launch_consumer(app, db, provider, cluster,
                               patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper

    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.launch_consumer()


@pytest.mark.skip(reason="rewrite needed")
def test_weave_expose_network(app, db, provider, cluster,
                              patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper

    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    weave.expose_network()


@pytest.mark.skip(reason="rewrite needed")
@pytest.mark.parametrize("type_", [
    "master",
    "consumer",
])
def test_weave_launch(app, db, provider, cluster, type_,
                      patched_salt, patched_sleep):
    from gluuapi.helper import WeaveHelper

    db.persist(cluster, "clusters")
    provider.type = type_
    weave = WeaveHelper(provider, app)
    weave.launch()


@pytest.mark.skip(reason="rewrite needed")
def test_weave_docker_bridge_ip(app, db, provider, cluster,
                                monkeypatch):
    from gluuapi.helper import WeaveHelper

    monkeypatch.setattr(
        "salt.utils.event.MasterEvent.get_event",
        lambda cls, wait, tag, full: {
            "tag": "salt/job",
            "data": {
                "retcode": 0,
                "return": "172.42.0.1",
            },
        },
    )

    db.persist(cluster, "clusters")
    weave = WeaveHelper(provider, app)
    assert weave.docker_bridge_ip() == "172.42.0.1"
