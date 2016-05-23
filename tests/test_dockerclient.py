# import os

import pytest


@pytest.mark.parametrize("retval, result", [
    (["sha256:aa5d5f5a81c90b8683085c027"], True),
    ([], False),
])
def test_image_exists(monkeypatch, dockerclient, retval, result):
    # stubbed ``docker.Client.images`` method's return value
    monkeypatch.setattr(
        "docker.Client.images",
        lambda cls, name, quiet: retval,
    )
    assert dockerclient.image_exists("busybox") is result


def test_run_container(monkeypatch, dockerclient):
    monkeypatch.setattr(
        "docker.Client.create_container",
        lambda cls, image, name, detach, environment, host_config, hostname: {"Id": "123"},
    )
    monkeypatch.setattr("docker.Client.start", lambda cls, container: "")
    assert dockerclient.run_container("abc", "gluuopendj") == "123"


def test_inspect_container(monkeypatch, dockerclient):
    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: [
            {
                "State": {
                    "Running": True,
                    "Paused": False,
                    "Restarting": False,
                    "OOMKilled": False,
                    "Dead": False,
                    "Pid": 0,
                    "ExitCode": 0,
                    "Error": "",
                    "StartedAt": "2015-11-21T04:44:28.74359245Z",
                    "FinishedAt": "2015-11-21T06:24:04.369726493Z"
                },
            }
        ]
    )
    assert len(dockerclient.inspect_container("weave"))


@pytest.mark.parametrize("stream_output, pulled", [
    (['{"stream":" ---\\u003e a9eb17255234\\n"}',
      '{"stream":"Successfully built 032b8b2855fc\\n"}'], True),
    (['{"stream":" ---\\u003e a9eb17255234\\n"}',
      '{"errorDetail": {}}'], False),
])
def test_pull_image(monkeypatch, dockerclient, stream_output, pulled):
    def gen(stream_output):
        for output in stream_output:
            yield output

    monkeypatch.setattr(
        "docker.Client.pull",
        lambda cls, repository, stream: gen(stream_output),
    )
    assert dockerclient.pull_image("gluuopendj") is pulled


def test_setup_container(monkeypatch, dockerclient):
    monkeypatch.setattr(
        "gluuapi.dockerclient.Docker.image_exists",
        lambda cls, image: False,
    )
    monkeypatch.setattr(
        "gluuapi.dockerclient.Docker.pull_image",
        lambda cls, image: True,
    )
    monkeypatch.setattr(
        "gluuapi.dockerclient.Docker.run_container",
        lambda cls, name, image, env, port_bindings, volumes, dns, dns_search, ulimits, hostname: "123",
    )
    assert dockerclient.setup_container("gluuopendj_123", "gluuopendj") == "123"


def test_remove_container(monkeypatch, dockerclient):
    monkeypatch.setattr(
        "docker.Client.remove_container",
        lambda cls, container, force: "gluuopendj_123",
    )
    assert dockerclient.remove_container("gluuopendj_123") == "gluuopendj_123"


@pytest.mark.skip(reason="implement me")
def test_copy_to_container(dockerclient):
    pass


@pytest.mark.skip(reason="implement me")
def test_copy_from_container(dockerclient):
    pass


def test_swarm_conf_str(dockerclient):
    expected = "--tlsverify --tlscacert=ca.pem --tlscert=cert.pem --tlskey=key.pem -H=tcp://10.10.10.10:3376"
    assert dockerclient._swarm_conf_str() == expected


@pytest.mark.skip(reason="implement me")
def test_exec_cmd(dockerclient):
    pass
