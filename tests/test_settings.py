def test_dev_config():
    from gluuengine.settings import DevConfig

    cfg = DevConfig()

    # sanity checks
    assert cfg.DEBUG is True


def test_test_config():
    from gluuengine.settings import TestConfig

    cfg = TestConfig()

    # sanity checks
    assert cfg.DEBUG is True
    assert cfg.TESTING is True


def test_prod_config():
    from gluuengine.settings import ProdConfig

    cfg = ProdConfig()

    # sanity checks
    assert cfg.DEBUG is False
