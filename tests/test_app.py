def test_get_config_object():
    from gluuengine.settings import ProdConfig
    from gluuengine.settings import DevConfig
    from gluuengine.settings import TestConfig
    from gluuengine.app import _get_config_object

    data = [
        ("prod", ProdConfig),
        ("test", TestConfig),
        ("anything", DevConfig),
    ]

    for item in data:
        assert _get_config_object(item[0]) == item[1]


def test_create_app():
    import os
    from gluuengine.app import create_app

    os.environ["API_ENV"] = "test"
    app = create_app()
    assert hasattr(app, "config")
