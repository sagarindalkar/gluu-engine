def test_create_log(app, db, container_log, oxauth_container):
    from gluuengine.model import ContainerLog

    oxauth_container.name = "oxauth-123"
    db.persist(oxauth_container, "containers")
    container_log.container_name = oxauth_container.name
    db.persist(container_log, "container_logs")
    assert ContainerLog.create_or_get(oxauth_container)


def test_get_log(app, db, container_log, oxauth_container):
    from gluuengine.model import ContainerLog

    oxauth_container.name = "oxauth-123"
    db.persist(oxauth_container, "containers")
    assert ContainerLog.create_or_get(oxauth_container)
