import codecs
import os

import pytest


@pytest.fixture(scope="session")
def config():
    from gluuapi.settings import TestConfig
    return TestConfig


@pytest.fixture(scope="session")
def app(request):
    from gluuapi.app import create_app
    from crochet import no_setup

    os.environ["API_ENV"] = "test"
    app = create_app()
    no_setup()
    return app


@pytest.fixture()
def db(request, app):
    from gluuapi.database import db

    db.init_app(app)

    def teardown():
        os.unlink(app.config["DATABASE_URI"])

    request.addfinalizer(teardown)
    return db


@pytest.fixture()
def cluster():
    from gluuapi.model import GluuCluster

    cluster = GluuCluster({
        "ox_cluster_hostname": "ox.example.com",
        "weave_ip_network": "10.20.10.0/24",
    })
    return cluster


@pytest.fixture()
def ldap_node(cluster, provider):
    from gluuapi.model import LdapNode

    node = LdapNode()
    node.id = "ldap_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    node.name = "ldap-node"
    return node


@pytest.fixture()
def oxauth_node(cluster, provider):
    from gluuapi.model import OxauthNode

    node = OxauthNode()
    node.id = "oxauth_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    return node


@pytest.fixture()
def oxtrust_node(cluster, provider):
    from gluuapi.model import OxtrustNode

    node = OxtrustNode()
    node.id = "oxtrust_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    return node


@pytest.fixture()
def provider():
    from gluuapi.model import Provider

    provider = Provider({
        "docker_base_url": "unix:///var/run/docker.sock",
        "hostname": "local",
    })
    return provider


@pytest.fixture()
def httpd_node(cluster, provider, oxauth_node, oxtrust_node):
    from gluuapi.model import HttpdNode

    node = HttpdNode()
    node.id = "httpd_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    node.name = "httpd-node"
    node.oxauth_node_id = oxauth_node.id
    node.oxtrust_node_id = oxtrust_node.id
    return node


@pytest.fixture
def patched_salt_cmd(monkeypatch):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )


@pytest.fixture
def patched_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda num: None)


@pytest.fixture()
def license_key():
    from gluuapi.model import LicenseKey

    key = LicenseKey({
        "name": "abc",
        "code": "abc",
        "public_key": "pub_key",
        "public_password": "pub_password",
        "license_password": "license_password"
    })
    return key


@pytest.fixture
def oxd_resp_ok(monkeypatch):
    class Response(object):
        ok = True
        text = ""
        status_code = 200

        def json(self):
            return {"license": "xyz"}
    monkeypatch.setattr("requests.post", lambda url, data: Response())


@pytest.fixture
def oxd_resp_err(monkeypatch):
    class Response(object):
        ok = False
        text = ""
        status_code = 400

        def json(self):
            return {"license": None}
    monkeypatch.setattr("requests.post", lambda url, data: Response())


@pytest.fixture
def validator_ok(monkeypatch):
    with codecs.open("tests/resource/validator_ok.txt", encoding="utf-8") as f:
        patch_output = f.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )


@pytest.fixture
def validator_err(monkeypatch):
    with codecs.open("tests/resource/validator_err.txt", encoding="utf-8") as f:
        patch_output = f.read()

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: patch_output,
    )


@pytest.fixture
def validator_expired(monkeypatch):
    from gluuapi.utils import timestamp_millis

    # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
    # ``decode_signed_license`` function,
    # hence we're monkeypatching ``gluuapi.utils.run`` directly
    monkeypatch.setattr(
        "gluuapi.utils.run",
        lambda cmd, exit_on_error: """Random line
{"valid":true,"metadata":{"expiration_date":{}}}""".format(timestamp_millis() - 1000000),
    )
