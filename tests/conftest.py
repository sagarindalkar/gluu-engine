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
def provider(cluster):
    from gluuapi.model import Provider

    provider = Provider({
        "docker_base_url": "unix:///var/run/docker.sock",
        "hostname": "gluu-master",
    })
    provider.cluster_id = cluster.id
    return provider


@pytest.fixture
def patched_salt(monkeypatch):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: {},
    )
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd_async",
        lambda cls, tgt, fun, arg: "",
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


@pytest.fixture
def salt_event_ok(monkeypatch):
    monkeypatch.setattr(
        "salt.utils.event.MasterEvent.get_event",
        lambda cls, wait, tag, full: {
            "tag": "salt/job",
            "data": {
                "retcode": 0,
                "return": "OK",
            },
        },
    )


@pytest.fixture()
def oxidp_node(cluster, provider):
    from gluuapi.model import OxidpNode

    node = OxidpNode()
    node.id = "oxidp_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    return node


@pytest.fixture()
def nginx_node(cluster, provider):
    from gluuapi.model import NginxNode

    node = NginxNode()
    node.id = "nginx_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    node.provider_id = provider.id
    return node


@pytest.fixture()
def docker_helper(request, app, provider):
    from gluuapi.helper.docker_helper import DockerHelper

    helper = DockerHelper(provider=provider)

    def teardown():
        helper.docker.close()

    request.addfinalizer(teardown)
    return helper


@pytest.fixture(scope="session")
def salt_helper():
    from gluuapi.helper.salt_helper import SaltHelper

    helper = SaltHelper()
    return helper


@pytest.fixture()
def ldap_setup(request, app, ldap_node, cluster):
    from gluuapi.setup import LdapSetup

    setup_obj = LdapSetup(ldap_node, cluster, app)

    def teardown():
        setup_obj.remove_build_dir()

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxauth_setup(request, app, oxauth_node, cluster):
    from gluuapi.setup import OxauthSetup

    setup_obj = OxauthSetup(oxauth_node, cluster, app)

    def teardown():
        setup_obj.remove_build_dir()

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxtrust_setup(request, app, oxtrust_node, cluster):
    from gluuapi.setup import OxtrustSetup

    setup_obj = OxtrustSetup(oxtrust_node, cluster, app)

    def teardown():
        setup_obj.remove_build_dir()

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxidp_setup(request, app, oxidp_node, cluster):
    from gluuapi.setup import OxidpSetup

    setup_obj = OxidpSetup(oxidp_node, cluster, app)

    def teardown():
        setup_obj.remove_build_dir()

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def nginx_setup(request, app, nginx_node, cluster):
    from gluuapi.setup import NginxSetup

    setup_obj = NginxSetup(nginx_node, cluster, app)

    def teardown():
        setup_obj.remove_build_dir()

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def patched_run(monkeypatch):
    monkeypatch.setattr(
        "subprocess.check_output",
        lambda cmd, stderr, shell, cwd: "",
    )


@pytest.fixture()
def node_log():
    from gluuapi.model import NodeLog

    node_log = NodeLog()
    node_log.id = "nginx_123"
    node_log.setup_log = node_log.id + "-setup.log"
    node_log.teardown_log = node_log.id + "-teardown.log"
    return node_log
