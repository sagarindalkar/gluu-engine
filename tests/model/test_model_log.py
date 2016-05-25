def test_create_log(db, container_log, ldap_container):
    from gluuengine.model import ContainerLog

    ldap_container.name = "ldap-123"
    db.persist(ldap_container, "containers")
    container_log.container_name = ldap_container.name
    db.persist(container_log, "container_logs")
    assert ContainerLog.create_or_get(ldap_container)


def test_get_log(db, container_log, ldap_container):
    from gluuengine.model import ContainerLog

    ldap_container.name = "ldap-123"
    db.persist(ldap_container, "containers")
    assert ContainerLog.create_or_get(ldap_container)
