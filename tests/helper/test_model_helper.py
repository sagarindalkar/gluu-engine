def test_ldap_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper.model_helper import LdapModelHelper
    from gluuapi.setup import LdapSetup
    from gluuapi.model import LdapNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = LdapModelHelper(cluster, provider, app)

        # some sanity checks
        assert helper.setup_class == LdapSetup
        assert helper.node_class == LdapNode
        assert helper.image == "gluuopendj"


def test_oxauth_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper import OxauthModelHelper
    from gluuapi.setup import OxauthSetup
    from gluuapi.model import OxauthNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = OxauthModelHelper(cluster, provider, app)

        # some sanity checks
        assert helper.setup_class == OxauthSetup
        assert helper.node_class == OxauthNode
        assert helper.image == "gluuoxauth"


def test_oxtrust_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper import OxtrustModelHelper
    from gluuapi.setup import OxtrustSetup
    from gluuapi.model import OxtrustNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )

    with app.test_request_context():
        helper = OxtrustModelHelper(cluster, provider, app)

        # some sanity checks
        assert helper.setup_class == OxtrustSetup
        assert helper.node_class == OxtrustNode
        assert helper.image == "gluuoxtrust"
