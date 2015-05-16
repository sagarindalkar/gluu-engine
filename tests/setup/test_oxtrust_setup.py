def test_setup(monkeypatch, oxtrust_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    monkeypatch.setattr("time.sleep", lambda num: None)

    # TODO: it might be better to split the tests
    oxtrust_setup.setup()


def test_delete_httpd_cert(monkeypatch, oxtrust_setup):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )
    oxtrust_setup.delete_httpd_cert()
