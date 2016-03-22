import pytest


def test_register_minion(monkeypatch, salt_helper):
    # stub unaccepted minion keys
    monkeypatch.setattr(
        "salt.key.Key.list_keys",
        lambda cls: {"minions_pre": ["abc"]},
    )

    # make sure minion key is accepted by checking whether
    # return value is not an empty ``dict``
    assert salt_helper.register_minion("abc") != {}


def test_unregister_minion(monkeypatch, salt_helper):
    # stub accepted minion keys
    monkeypatch.setattr(
        "salt.key.Key.list_keys",
        lambda cls: {"minions": ["abc"]},
    )

    # make sure minion key is deleted by checking whether
    # return value is not an empty ``dict``
    assert salt_helper.unregister_minion("abc") != {}


def test_is_minion_registered(monkeypatch, salt_helper):
    # stub accepted minion keys
    monkeypatch.setattr(
        "salt.key.Key.list_keys",
        lambda cls: {"minions": ["abc"]},
    )

    # make sure minion key is already accepted
    assert salt_helper.is_minion_registered("abc") is True


def test_copy_file(monkeypatch, salt_helper, patched_sleep):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: {"123": {"/tmp/sample.txt": True}},
    )
    src = "tests/helper/sample.txt"
    dest = "/tmp/sample.txt"
    assert salt_helper.copy_file("123", src, dest)


def test_reject_minion(monkeypatch, salt_helper):
    # stub accepted minion keys
    monkeypatch.setattr(
        "salt.key.Key.list_keys",
        lambda cls: {"minions": ["abc"]},
    )

    # make sure minion key is rejected by checking whether
    # return value is not an empty ``dict``
    assert salt_helper.reject_minion("abc") != {}


def test_subscribe_event_no_response(salt_helper, provider, monkeypatch):
    import gluuapi.errors

    monkeypatch.setattr(
        "salt.utils.event.MasterEvent.get_event",
        lambda cls, wait, tag, full: None,
    )
    jid = salt_helper.cmd_async(provider.hostname, "cmd.run", ["echo test"])
    with pytest.raises(gluuapi.errors.SaltEventError):
        salt_helper.subscribe_event(jid, provider.hostname)


def test_subscribe_event_no_skip_retcode(salt_helper, provider, monkeypatch):
    import gluuapi.errors

    monkeypatch.setattr(
        "salt.utils.event.MasterEvent.get_event",
        lambda cls, wait, tag, full: {
            "tag": "salt/job",
            "data": {
                "retcode": 100,
                "return": "OK",
            },
        },
    )
    jid = salt_helper.cmd_async(provider.hostname, "cmd.run", ["echo test"])
    with pytest.raises(gluuapi.errors.SaltEventError):
        salt_helper.subscribe_event(jid, provider.hostname)
