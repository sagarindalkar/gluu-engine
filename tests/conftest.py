import os

import pytest


@pytest.fixture(scope="session")
def config():
    from api.settings import TestConfig
    return TestConfig


@pytest.fixture(scope="session")
def app(request):
    from api.app import create_app
    from api.settings import TestConfig

    app = create_app(TestConfig)
    return app


@pytest.fixture()
def db(request, app):
    from api.database import db

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
    from api.model import GluuCluster

    cluster = GluuCluster()
    return cluster


@pytest.fixture(scope="session")
def ldap_node(cluster):
    from api.model import ldapNode

    node = ldapNode()
    node.id = "ldap_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture()
def oxauth_node(cluster):
    from api.model import oxauthNode

    node = oxauthNode()
    node.id = "oxauth_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture(scope="session")
def oxtrust_node(cluster):
    from api.model import oxtrustNode

    node = oxtrustNode()
    node.id = "oxtrust_{}_123".format(cluster.id)
    node.cluster_id = cluster.id
    return node


@pytest.fixture(scope="session")
def provider():
    from api.model import Provider

    provider = Provider({
        "base_url": "unix:///var/run/docker.sock",
        "name": "local",
    })
    return provider
