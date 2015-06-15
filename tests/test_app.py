def test_get_config_object():
    from gluuapi.settings import ProdConfig
    from gluuapi.settings import DevConfig
    from gluuapi.settings import TestConfig
    from gluuapi.app import _get_config_object

    data = [
        ("prod", ProdConfig),
        ("test", TestConfig),
        ("anything", DevConfig),
    ]

    for item in data:
        assert _get_config_object(item[0]) == item[1]
