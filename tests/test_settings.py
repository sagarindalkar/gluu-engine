def test_dev_config():
    from gluuapi.settings import DevConfig

    cfg = DevConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.LOG_DIR == "/tmp/gluu-dev"
    assert cfg.DATA_DIR.endswith("/.gluu-cluster")
    assert cfg.DATABASE_URI.endswith("/.gluu-cluster/db/db_dev.json")
    assert cfg.INSTANCE_DIR.endswith("/.gluu-cluster/instance")


def test_test_config():
    from gluuapi.settings import TestConfig

    cfg = TestConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.TESTING is True
    assert cfg.LOG_DIR == "/tmp/gluu-test"
    assert cfg.DATA_DIR.endswith("/.gluu-cluster")
    assert cfg.DATABASE_URI.endswith("/.gluu-cluster/db/db_test.json")
    assert cfg.INSTANCE_DIR.endswith("/.gluu-cluster/instance")


def test_prod_config():
    from gluuapi.settings import ProdConfig

    cfg = ProdConfig()

    # sanity checks
    assert cfg.DEBUG is False
    assert cfg.LOG_DIR == "/var/log/gluu"
    assert cfg.DATA_DIR == "/var/lib/gluu-cluster"
    assert cfg.DATABASE_URI == "/var/lib/gluu-cluster/db/db.json"
    assert cfg.INSTANCE_DIR == "/var/lib/gluu-cluster/instance"
    assert cfg.DOCKER_CERT_DIR == "/var/lib/gluu-cluster/docker_certs"
