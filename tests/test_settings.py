def test_dev_config():
    from gluuengine.settings import DevConfig

    cfg = DevConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.DATABASE_URI == "/var/lib/gluuengine/db/db_dev.json"


def test_test_config():
    from gluuengine.settings import TestConfig

    cfg = TestConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.TESTING is True
    assert cfg.DATABASE_URI == "/var/lib/gluuengine/db/db_test.json"


def test_prod_config():
    from gluuengine.settings import ProdConfig

    cfg = ProdConfig()

    # sanity checks
    assert cfg.DEBUG is False
    assert cfg.LOG_DIR == "/var/log/gluuengine"
    assert cfg.DATA_DIR == "/var/lib/gluuengine"
    assert cfg.DATABASE_URI == "/var/lib/gluuengine/db/db.json"
    assert cfg.INSTANCE_DIR == "/var/lib/gluuengine/instance"
    assert cfg.CUSTOM_LDAP_SCHEMA_DIR == "/var/lib/gluuengine/custom/opendj/schema"
