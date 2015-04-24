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


def test_file_dict(salt_helper):
    fn = "tests/helper/sample.txt"
    actual = salt_helper._file_dict(fn)
    expected = {fn: "example\n"}
    assert actual == expected


def test_load_files(salt_helper):
    fn = "tests/helper/sample.txt"
    actual = salt_helper._load_files([fn])
    expected = {fn: "example\n"}
    assert actual == expected


def test_load_files_error(salt_helper):
    fn = "tests/helper"
    with pytest.raises(ValueError):
        salt_helper._load_files([fn])


def test_copy_file(monkeypatch, salt_helper):
    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: {"123": {"/tmp/sample.txt": True}},
    )
    src = "tests/helper/sample.txt"
    dest = "/tmp/sample.txt"
    assert salt_helper.copy_file("123", src, dest)
