# import codecs
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
        try:
            os.unlink(app.config["DATABASE_URI"])
        except OSError:
            pass

    request.addfinalizer(teardown)
    return db


@pytest.fixture()
def cluster():
    from gluuapi.model import Cluster

    cluster = Cluster({
        "ox_cluster_hostname": "ox.example.com",
    })
    return cluster


@pytest.fixture()
def master_node():
    from gluuapi.model import MasterNode

    node = MasterNode()
    node.populate({
        "name": "master-node",
        "type": "master",
    })
    return node


@pytest.fixture()
def worker_node():
    from gluuapi.model import WorkerNode

    node = WorkerNode()
    node.populate({
        "name": "worker-node",
        "type": "worker",
    })
    return node


@pytest.fixture()
def discovery_node():
    from gluuapi.model import DiscoveryNode

    node = DiscoveryNode()
    node.populate({
        "name": "discovery-node",
        "type": "discovery",
    })
    return node


@pytest.fixture()
def ldap_container(cluster, master_node):
    from gluuapi.model import LdapContainer

    ctr = LdapContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    ctr.name = "ldap-node"
    return ctr


@pytest.fixture()
def oxauth_container(cluster, master_node):
    from gluuapi.model import OxauthContainer

    ctr = OxauthContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxtrust_container(cluster, master_node):
    from gluuapi.model import OxtrustContainer

    ctr = OxtrustContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxidp_container(cluster, master_node):
    from gluuapi.model import OxidpContainer

    ctr = OxidpContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def nginx_container(cluster, master_node):
    from gluuapi.model import NginxContainer

    ctr = NginxContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxasimba_container(cluster, master_node):
    from gluuapi.model import OxasimbaContainer

    ctr = OxasimbaContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def generic_provider(cluster):
    from gluuapi.model import GenericProvider

    provider = GenericProvider()
    provider.populate({
        "name": "generic_provider",
    })
    return provider

@pytest.fixture()
def digitalocean_provider(cluster):
    from gluuapi.model import DigitalOceanProvider

    provider = DigitalOceanProvider()
    provider.populate({
        "name": "digitalocean_provider",
    })
    return provider


# @pytest.fixture
# def patched_sleep(monkeypatch):
#     monkeypatch.setattr("time.sleep", lambda num: None)


@pytest.fixture()
def license_key():
    from gluuapi.model import LicenseKey

    key = LicenseKey()
    key.populate({
        "name": "abc",
        "code": "abc",
        "public_key": "pub_key",
        "public_password": "pub_password",
        "license_password": "license_password"
    })
    return key


# @pytest.fixture
# def oxd_resp_ok(monkeypatch):
#     class Response(object):
#         ok = True
#         text = ""
#         status_code = 200

#         def json(self):
#             return {"license": "xyz"}
#     monkeypatch.setattr("requests.post", lambda url, data: Response())


# @pytest.fixture
# def oxd_resp_err(monkeypatch):
#     class Response(object):
#         ok = False
#         text = ""
#         status_code = 400

#         def json(self):
#             return {"license": None}
#     monkeypatch.setattr("requests.post", lambda url, data: Response())


# @pytest.fixture
# def validator_ok(monkeypatch):
#     with codecs.open("tests/resource/validator_ok.txt", encoding="utf-8") as f:
#         patch_output = f.read()

#     # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuapi.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuapi.utils.run",
#         lambda cmd, exit_on_error: patch_output,
#     )


# @pytest.fixture
# def validator_err(monkeypatch):
#     with codecs.open("tests/resource/validator_err.txt", encoding="utf-8") as f:
#         patch_output = f.read()

#     # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuapi.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuapi.utils.run",
#         lambda cmd, exit_on_error: patch_output,
#     )


# @pytest.fixture
# def validator_expired(monkeypatch):
#     from gluuapi.utils import timestamp_millis

#     # cannot monkeypatch ``gluuapi.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuapi.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuapi.utils.run",
#         lambda cmd, exit_on_error: """Random line
# {"valid":true,"metadata":{"expiration_date":{}}}""".format(timestamp_millis() - 1000000),
#     )


@pytest.fixture()
def dockerclient(request):
    from collections import namedtuple
    from gluuapi.dockerclient import Docker

    FakeTLS = namedtuple("TLS", ["ca_cert", "cert"])

    config = {}
    swarm_config = {
        "tls": FakeTLS(ca_cert="ca.pem", cert=("cert.pem", "key.pem",)),
        "base_url": "https://10.10.10.10:3376",
    }
    client = Docker(config, swarm_config)
    return client


# @pytest.fixture()
# def ldap_setup(request, app, ldap_node, cluster, db, provider):
#     from gluuapi.setup import LdapSetup

#     db.persist(provider, "providers")
#     setup_obj = LdapSetup(ldap_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxauth_setup(request, app, oxauth_node, cluster, db, provider):
#     from gluuapi.setup import OxauthSetup

#     db.persist(provider, "providers")
#     setup_obj = OxauthSetup(oxauth_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxtrust_setup(request, app, oxtrust_node, cluster, db, provider):
#     from gluuapi.setup import OxtrustSetup

#     db.persist(provider, "providers")
#     setup_obj = OxtrustSetup(oxtrust_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxidp_setup(request, app, oxidp_node, cluster, db, provider):
#     from gluuapi.setup import OxidpSetup

#     db.persist(provider, "providers")
#     setup_obj = OxidpSetup(oxidp_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def nginx_setup(request, app, nginx_node, cluster, db, provider):
#     from gluuapi.setup import NginxSetup

#     db.persist(provider, "providers")
#     setup_obj = NginxSetup(nginx_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def patched_run(monkeypatch):
#     monkeypatch.setattr(
#         "subprocess.check_output",
#         lambda cmd, stderr, shell, cwd: "",
#     )


@pytest.fixture()
def container_log():
    from gluuapi.model import ContainerLog

    log = ContainerLog()
    log.setup_log = log.id + "-setup.log"
    log.teardown_log = log.id + "-teardown.log"
    return log


# @pytest.fixture()
# def patched_exec_cmd(monkeypatch):
#     from gluuapi.helper.docker_helper import DockerExecResult

#     monkeypatch.setattr(
#         "gluuapi.helper.DockerHelper.exec_cmd",
#         lambda cls, container, cmd: DockerExecResult(cmd, 0, ""),
#     )
