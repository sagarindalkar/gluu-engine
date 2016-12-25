# import codecs
import os

import pytest


@pytest.fixture(scope="session")
def config():
    from gluuengine.settings import TestConfig
    return TestConfig


@pytest.fixture(scope="session")
def app(request):
    from gluuengine.app import create_app
    from crochet import no_setup

    no_setup()
    os.environ["API_ENV"] = "test"
    app = create_app()
    return app


@pytest.fixture(scope="session")
def db(request, app):
    from gluuengine.database import db

    db.init_app(app)

    def teardown():
        try:
            os.unlink(app.config["SHARED_DATABASE_URI"])
        except OSError:
            pass

        with app.app_context():
            db.backend.cx.drop_database(db.backend.db.name)

    request.addfinalizer(teardown)
    return db


@pytest.fixture()
def cluster():
    from gluuengine.model import Cluster

    cluster = Cluster({
        "ox_cluster_hostname": "ox.example.com",
    })
    return cluster


@pytest.fixture()
def master_node():
    from gluuengine.model import MasterNode

    node = MasterNode({
        "name": "master-node",
        "type": "master",
    })
    return node


@pytest.fixture()
def worker_node():
    from gluuengine.model import WorkerNode

    node = WorkerNode({
        "name": "worker-node",
        "type": "worker",
    })
    return node


@pytest.fixture()
def discovery_node():
    from gluuengine.model import DiscoveryNode

    node = DiscoveryNode({
        "name": "discovery-node",
        "type": "discovery",
    })
    return node


@pytest.fixture()
def oxauth_container(cluster, master_node):
    from gluuengine.model import OxauthContainer

    ctr = OxauthContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxtrust_container(cluster, master_node):
    from gluuengine.model import OxtrustContainer

    ctr = OxtrustContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxidp_container(cluster, master_node):
    from gluuengine.model import OxidpContainer

    ctr = OxidpContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def nginx_container(cluster, master_node):
    from gluuengine.model import NginxContainer

    ctr = NginxContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def oxasimba_container(cluster, master_node):
    from gluuengine.model import OxasimbaContainer

    ctr = OxasimbaContainer()
    ctr.cluster_id = cluster.id
    ctr.node_id = master_node.id
    return ctr


@pytest.fixture()
def generic_provider(cluster):
    from gluuengine.model import GenericProvider

    provider = GenericProvider({
        "name": "generic_provider",
    })
    return provider

@pytest.fixture()
def digitalocean_provider(cluster):
    from gluuengine.model import DigitalOceanProvider

    provider = DigitalOceanProvider({
        "name": "digitalocean_provider",
        "driver_attrs": {
            "digitalocean_image": "ubuntu-14-04-x64",
            "digitalocean_ipv6": False,
        },
    })
    return provider


@pytest.fixture
def patched_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda num: None)


@pytest.fixture()
def license_key():
    from gluuengine.model import LicenseKey

    key = LicenseKey({
        "name": "abc",
        "code": "abc",
        "metadata": {},
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

#     # cannot monkeypatch ``gluuengine.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuengine.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuengine.utils.run",
#         lambda cmd, exit_on_error: patch_output,
#     )


# @pytest.fixture
# def validator_err(monkeypatch):
#     with codecs.open("tests/resource/validator_err.txt", encoding="utf-8") as f:
#         patch_output = f.read()

#     # cannot monkeypatch ``gluuengine.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuengine.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuengine.utils.run",
#         lambda cmd, exit_on_error: patch_output,
#     )


# @pytest.fixture
# def validator_expired(monkeypatch):
#     from gluuengine.utils import timestamp_millis

#     # cannot monkeypatch ``gluuengine.utils.run`` function wrapped in
#     # ``decode_signed_license`` function,
#     # hence we're monkeypatching ``gluuengine.utils.run`` directly
#     monkeypatch.setattr(
#         "gluuengine.utils.run",
#         lambda cmd, exit_on_error: """Random line
# {"valid":true,"metadata":{"expiration_date":{}}}""".format(timestamp_millis() - 1000000),
#     )


@pytest.fixture()
def swarm_config():
    from collections import namedtuple

    FakeTLS = namedtuple("TLS", ["ca_cert", "cert"])

    swarm_config = {
        "tls": FakeTLS(ca_cert="ca.pem", cert=("cert.pem", "key.pem",)),
        "base_url": "https://10.10.10.10:3376",
    }
    return swarm_config


@pytest.fixture()
def dockerclient(swarm_config):
    from gluuengine.dockerclient import Docker

    config = {}
    swarm_config = swarm_config
    client = Docker(config, swarm_config)
    return client


# @pytest.fixture()
# def ldap_setup(request, app, ldap_node, cluster, db, provider):
#     from gluuengine.setup import LdapSetup

#     db.persist(provider, "providers")
#     setup_obj = LdapSetup(ldap_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxauth_setup(request, app, oxauth_node, cluster, db, provider):
#     from gluuengine.setup import OxauthSetup

#     db.persist(provider, "providers")
#     setup_obj = OxauthSetup(oxauth_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxtrust_setup(request, app, oxtrust_node, cluster, db, provider):
#     from gluuengine.setup import OxtrustSetup

#     db.persist(provider, "providers")
#     setup_obj = OxtrustSetup(oxtrust_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def oxidp_setup(request, app, oxidp_node, cluster, db, provider):
#     from gluuengine.setup import OxidpSetup

#     db.persist(provider, "providers")
#     setup_obj = OxidpSetup(oxidp_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


# @pytest.fixture()
# def nginx_setup(request, app, nginx_node, cluster, db, provider):
#     from gluuengine.setup import NginxSetup

#     db.persist(provider, "providers")
#     setup_obj = NginxSetup(nginx_node, cluster, app)

#     def teardown():
#         setup_obj.remove_build_dir()

#     request.addfinalizer(teardown)
#     return setup_obj


@pytest.fixture()
def patched_po_run(monkeypatch):
    monkeypatch.setattr(
        "subprocess.Popen.communicate",
        lambda cls: ("", "",),
    )


@pytest.fixture()
def container_log():
    from gluuengine.model import ContainerLog

    log = ContainerLog()
    log.setup_log = log.id + "-setup.log"
    log.teardown_log = log.id + "-teardown.log"
    return log


@pytest.fixture()
def patched_exec_cmd(monkeypatch):
    from gluuengine.dockerclient._docker import DockerExecResult

    monkeypatch.setattr(
        "gluuengine.dockerclient.Docker.exec_cmd",
        lambda cls, container, cmd: DockerExecResult(cmd, 0, ""),
    )


@pytest.fixture()
def base_setup(monkeypatch, app, db, swarm_config,
               cluster, oxauth_container, master_node):
    from gluuengine.setup.base import BaseSetup

    class FakeBaseSetup(BaseSetup):
        def setup(self):
            pass

    monkeypatch.setattr(
        "gluuengine.machine.Machine.config",
        lambda cls, name: {},
    )
    monkeypatch.setattr(
        "gluuengine.machine.Machine.swarm_config",
        lambda cls, name: swarm_config,
    )

    db.persist(master_node, "nodes")
    return FakeBaseSetup(oxauth_container, cluster, app)


@pytest.fixture()
def ox_setup(monkeypatch, app, db, swarm_config,
             cluster, oxauth_container, master_node):
    from gluuengine.setup.base import OxSetup

    monkeypatch.setattr(
        "gluuengine.machine.Machine.config",
        lambda cls, name: {},
    )
    monkeypatch.setattr(
        "gluuengine.machine.Machine.swarm_config",
        lambda cls, name: swarm_config,
    )

    db.persist(master_node, "nodes")
    return OxSetup(oxauth_container, cluster, app)
