import os

import pytest


@pytest.fixture(scope="session")
def config():
    from gluuapi.settings import TestConfig
    return TestConfig


@pytest.fixture(scope="session")
def app(request):
    from gluuapi.app import create_app
    from gluuapi.settings import TestConfig

    app = create_app(TestConfig)
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
    from gluuapi.model import GluuCluster

    cluster = GluuCluster()
    cluster.hostname_oxauth_cluster = "oxauth.example.com"
    cluster.hostname_oxtrust_cluster = "oxtrust.example.com"
    return cluster


@pytest.fixture()
def ldap_node(cluster):
    from gluuapi.model import ldapNode

    node = ldapNode()
    node.id = "ldap_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture()
def oxauth_node(cluster):
    from gluuapi.model import oxauthNode

    node = oxauthNode()
    node.id = "oxauth_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture()
def oxtrust_node(cluster):
    from gluuapi.model import oxtrustNode

    node = oxtrustNode()
    node.id = "oxtrust_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture()
def provider():
    from gluuapi.model import Provider

    provider = Provider({
        "base_url": "unix:///var/run/docker.sock",
        "name": "local",
    })
    return provider
