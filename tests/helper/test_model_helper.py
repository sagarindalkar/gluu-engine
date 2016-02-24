def test_ldap_model_helper(monkeypatch, app, cluster, provider, db, ldap_node):
    from gluuapi.helper.model_helper import LdapModelHelper
    from gluuapi.setup import LdapSetup
    from gluuapi.model import LdapNode

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    ldap_node.provider_id = provider.id
    ldap_node.cluster_id = cluster.id
    db.persist(ldap_node, "nodes")

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = LdapModelHelper(ldap_node, app)

        # some sanity checks
        assert helper.setup_class == LdapSetup
        assert helper.node_class == LdapNode
        assert helper.image == "gluuopendj"


def test_oxauth_model_helper(monkeypatch, app, cluster, provider,
                             oxauth_node, db):
    from gluuapi.helper import OxauthModelHelper
    from gluuapi.setup import OxauthSetup
    from gluuapi.model import OxauthNode

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    oxauth_node.provider_id = provider.id
    oxauth_node.cluster_id = cluster.id
    db.persist(oxauth_node, "nodes")

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = OxauthModelHelper(oxauth_node, app)

        # some sanity checks
        assert helper.setup_class == OxauthSetup
        assert helper.node_class == OxauthNode
        assert helper.image == "gluuoxauth"


def test_oxtrust_model_helper(monkeypatch, app, cluster, provider,
                              oxtrust_node, db):
    from gluuapi.helper import OxtrustModelHelper
    from gluuapi.setup import OxtrustSetup
    from gluuapi.model import OxtrustNode

    db.persist(cluster, "clusters")
    db.persist(provider, "providers")
    oxtrust_node.provider_id = provider.id
    oxtrust_node.cluster_id = cluster.id
    db.persist(oxtrust_node, "nodes")

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = OxtrustModelHelper(oxtrust_node, app)

        # some sanity checks
        assert helper.setup_class == OxtrustSetup
        assert helper.node_class == OxtrustNode
        assert helper.image == "gluuoxtrust"
