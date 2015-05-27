import pytest


def test_base_model_helper_init(app, cluster, provider):
    from gluuapi.helper.model_helper import BaseModelHelper

    # instantiating BaseModelHelper without overriding any
    # required attrs (e.g. ``setup_class``) raises AssertionError
    with pytest.raises(AssertionError):
        BaseModelHelper(cluster, provider, "127.0.0.1",
                        template_dir=app.config["TEMPLATES_DIR"],
                        log_dir=app.config["LOG_DIR"],
                        )


def test_ldap_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper.model_helper import LdapModelHelper
    from gluuapi.setup import LdapSetup
    from gluuapi.model import LdapNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )
    helper = LdapModelHelper(cluster, provider, "127.0.0.1",
                             template_dir=app.config["TEMPLATES_DIR"],
                             log_dir=app.config["LOG_DIR"],
                             )

    # some sanity checks
    assert helper.setup_class == LdapSetup
    assert helper.node_class == LdapNode
    assert helper.image == "gluuopendj"
    assert helper.dockerfile == "https://raw.githubusercontent.com" \
                                "/GluuFederation/gluu-docker/master" \
                                "/ubuntu/14.04/gluuopendj/Dockerfile"

    helper.prepare_node_attrs()
    assert helper.node.ip == ipaddr


def test_oxauth_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper import OxauthModelHelper
    from gluuapi.setup import OxauthSetup
    from gluuapi.model import OxauthNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )
    helper = OxauthModelHelper(cluster, provider, "127.0.0.1",
                               template_dir=app.config["TEMPLATES_DIR"],
                               log_dir=app.config["LOG_DIR"],
                               )

    # some sanity checks
    assert helper.setup_class == OxauthSetup
    assert helper.node_class == OxauthNode
    assert helper.image == "gluuoxauth"
    assert helper.dockerfile == "https://raw.githubusercontent.com" \
                                "/GluuFederation/gluu-docker/master" \
                                "/ubuntu/14.04/gluuoxauth/Dockerfile"

    helper.prepare_node_attrs()
    assert helper.node.ip == ipaddr


def test_oxtrust_model_helper(monkeypatch, app, cluster, provider):
    from gluuapi.helper import OxtrustModelHelper
    from gluuapi.setup import OxtrustSetup
    from gluuapi.model import OxtrustNode

    ipaddr = "172.17.0.4"
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )
    helper = OxtrustModelHelper(cluster, provider, "127.0.0.1",
                                template_dir=app.config["TEMPLATES_DIR"],
                                log_dir=app.config["LOG_DIR"],
                                )

    # some sanity checks
    assert helper.setup_class == OxtrustSetup
    assert helper.node_class == OxtrustNode
    assert helper.image == "gluuoxtrust"
    assert helper.dockerfile == "https://raw.githubusercontent.com" \
                                "/GluuFederation/gluu-docker/master" \
                                "/ubuntu/14.04/gluuoxtrust/Dockerfile"

    helper.prepare_node_attrs()
    assert helper.node.ip == ipaddr
