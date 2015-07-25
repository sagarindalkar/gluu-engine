import pytest


def test_init_invalid_provider(app):
    from gluuapi.task import RecoverProviderTask

    with pytest.raises(SystemExit):
        RecoverProviderTask(app, "random")


def test_container_stopped(monkeypatch, app, db, cluster, provider):
    from gluuapi.task import RecoverProviderTask

    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, cid: {"State": {"Running": False}})

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    recovery = RecoverProviderTask(app, provider.id)
    assert recovery.container_stopped("weave") is True


def test_node_setup(patched_salt_cmd, db, app, cluster, provider,
                    ldap_node, oxauth_node, oxtrust_node, httpd_node):
    from gluuapi.task import RecoverProviderTask

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")

    # needed by oxauth_node test
    ldap_node.state = "SUCCESS"
    db.persist(ldap_node, "nodes")

    # needed by oxtrust_node test
    httpd_node.oxtrust_node_id = oxtrust_node.id
    db.persist(httpd_node, "nodes")

    task = RecoverProviderTask(app, provider.id)

    for node in [ldap_node, oxauth_node, oxtrust_node, httpd_node]:
        task.node_setup(node)
