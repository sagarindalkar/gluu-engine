import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_ldap_container_helper(monkeypatch, app, cluster, master_node,
                               db, ldap_container, swarm_config):
    from gluuengine.helper.container_helper import LdapContainerHelper
    from gluuengine.setup import LdapSetup

    monkeypatch.setattr(
        "gluuengine.machine.Machine._config",
        lambda cls, cmd, name, docker_friendly: swarm_config,
    )

    with app.app_context():
        db.persist(cluster, "clusters")
        db.persist(master_node, "nodes")
        ldap_container.node_id = master_node.id
        ldap_container.cluster_id = cluster.id
        db.persist(ldap_container, "containers")

        helper = LdapContainerHelper(ldap_container, app)

        # some sanity checks
        assert helper.setup_class == LdapSetup


@pytest.mark.skip(reason="rewrite needed")
def test_oxauth_container_helper(monkeypatch, app, cluster, master_node,
                                 oxauth_container, db, swarm_config):
    from gluuengine.helper import OxauthContainerHelper
    from gluuengine.setup import OxauthSetup

    monkeypatch.setattr(
        "gluuengine.machine.Machine._config",
        lambda cls, cmd, name, docker_friendly: swarm_config,
    )

    with app.app_context():
        db.persist(cluster, "clusters")
        db.persist(master_node, "nodes")
        oxauth_container.master_node_id = master_node.id
        oxauth_container.cluster_id = cluster.id
        db.persist(oxauth_container, "nodes")

        helper = OxauthContainerHelper(oxauth_container, app)

        # some sanity checks
        assert helper.setup_class == OxauthSetup


@pytest.mark.skip(reason="rewrite needed")
def test_oxtrust_container_helper(monkeypatch, app, cluster, master_node,
                                  oxtrust_container, db, swarm_config):
    from gluuengine.helper import OxtrustContainerHelper
    from gluuengine.setup import OxtrustSetup

    monkeypatch.setattr(
        "gluuengine.machine.Machine._config",
        lambda cls, cmd, name, docker_friendly: swarm_config,
    )

    with app.app_context():
        db.persist(cluster, "clusters")
        db.persist(master_node, "nodes")
        oxtrust_container.node_id = master_node.id
        oxtrust_container.cluster_id = cluster.id
        db.persist(oxtrust_container, "nodes")

        helper = OxtrustContainerHelper(oxtrust_container, app)

        # some sanity checks
        assert helper.setup_class == OxtrustSetup
