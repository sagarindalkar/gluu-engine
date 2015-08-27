def test_dev_config():
    from gluuapi.settings import DevConfig

    cfg = DevConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.LOG_DIR == "/var/log/gluu-dev"
    assert cfg.DATA_DIR == "/var/lib/gluu-cluster-dev"
    assert cfg.DATABASE_URI == "/var/lib/gluu-cluster-dev/db/db_dev.json"
    assert cfg.INSTANCE_DIR == "/var/lib/gluu-cluster-dev/instance"
    assert cfg.DOCKER_CERT_DIR == "/var/lib/gluu-cluster-dev/docker_certs"


def test_test_config():
    from gluuapi.settings import TestConfig

    cfg = TestConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.TESTING is True
    assert cfg.LOG_DIR == "/var/log/gluu-test"
    assert cfg.DATA_DIR == "/var/lib/gluu-cluster-test"
    assert cfg.DATABASE_URI == "/var/lib/gluu-cluster-test/db/db_test.json"
    assert cfg.INSTANCE_DIR == "/var/lib/gluu-cluster-test/instance"
    assert cfg.DOCKER_CERT_DIR == "/var/lib/gluu-cluster-test/docker_certs"


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
