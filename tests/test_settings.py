import os.path


def test_dev_config():
    from gluuapi.settings import DevConfig

    cfg = DevConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.LOG_DIR == "/tmp/gluu-dev"
    assert cfg.DATA_DIR == os.path.expanduser('~') + '/.gluu-cluster'
    assert cfg.DATABASE_URI == os.path.join(cfg.DATA_DIR, "db", "db_dev.json")


def test_test_config():
    from gluuapi.settings import TestConfig

    cfg = TestConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.LOG_DIR == "/tmp/gluu-test"
    assert cfg.DATA_DIR == os.path.expanduser('~') + '/.gluu-cluster'
    assert cfg.DATABASE_URI == os.path.join(cfg.DATA_DIR, "db", "db_test.json")


def test_prod_config():
    from gluuapi.settings import ProdConfig

    cfg = ProdConfig()

    # sanity checks
    assert cfg.DEBUG is False
    assert cfg.LOG_DIR == "/var/log/gluu"
    assert cfg.DATA_DIR == "/var/lib/gluu-cluster"
    assert cfg.DATABASE_URI == os.path.join(cfg.DATA_DIR, "db", "db.json")
