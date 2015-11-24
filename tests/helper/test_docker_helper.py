import os.path
import shutil
from collections import namedtuple


FakeResp = namedtuple("FakeReps", ["status_code", "text"])


def test_image_exists_found(monkeypatch, docker_helper):
    # stubbed ``docker.Client.images`` method's return value
    monkeypatch.setattr(
        "docker.Client.images",
        lambda cls, name: [
            {
                'Created': 1401926735,
                'Id': 'a9eb172552348a9a49180694790b33a1097f546456d041b6e82e4d',
                'ParentId': '120e218dd395ec314e7b6249f39d2853911b3d6def6ea164',
                'RepoTags': ['busybox:buildroot-2014.02', 'busybox:latest'],
                'Size': 0,
                'VirtualSize': 2433303,
            }
        ],
    )
    assert docker_helper.image_exists("busybox") is True


def test_image_exists_notfound(monkeypatch, docker_helper):
    # stubbed ``docker.Client.images`` method's return value
    monkeypatch.setattr("docker.Client.images", lambda cls, name: [])
    assert docker_helper.image_exists("busybox") is False


def test_get_container_ip(monkeypatch, docker_helper):
    ipaddr = "172.17.0.4"

    monkeypatch.setattr(
        "docker.Client.inspect_container",
        lambda cls, container: {"NetworkSettings": {"IPAddress": ipaddr}},
    )
    assert docker_helper.get_container_ip("abc") == ipaddr


def test_build_image_success(monkeypatch, docker_helper):
    stream_output = [
        '{"stream":" ---\\u003e a9eb17255234\\n"}',
        '{"stream":"Successfully built 032b8b2855fc\\n"}'
    ]

    def gen(stream_output):
        for output in stream_output:
            yield output

    monkeypatch.setattr(
        "docker.Client.build",
        lambda cls, path, tag, quiet, rm, forcerm, pull: gen(stream_output),
    )
    assert docker_helper.build_image("/tmp/abc", "abc") is True


def test_build_image_failed(monkeypatch, docker_helper):
    stream_output = [
        '{"stream":" ---\\u003e a9eb17255234\\n"}',
        '{"errorDetail": {}}'
    ]

    def gen(stream_output):
        for output in stream_output:
            yield output

    monkeypatch.setattr(
        "docker.Client.build",
        lambda cls, path, tag, quiet, rm, forcerm, pull: gen(stream_output),
    )
    assert docker_helper.build_image("/tmp/abc", "abc") is False


def test_run_container(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "docker.Client.create_container",
        lambda cls, image, name, detach, environment, host_config: {"Id": "123"},
    )
    monkeypatch.setattr("docker.Client.start", lambda cls, container: "")
    assert docker_helper.run_container("abc", "gluuopendj") == "123"


def test_build_gluubase(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.image_exists",
        lambda cls, name: [{
            'Created': 1401926735,
            'Id': 'a9eb172552348a9a49180694790b33a1097f546456d041b6e82e4d',
            'ParentId': '120e218dd395ec314e7b6249f39d2853911b3d6def6ea164',
            'RepoTags': ['gluubase:latest'],
            'Size': 0,
            'VirtualSize': 2433303,
        }],
    )
    assert docker_helper._build_gluubase() is True


def test_build_gluubase_no_image(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.image_exists",
        lambda cls, name: [],
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.get_remote_files",
        lambda cls, *files: "/tmp/gluuopendj",
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.build_image",
        lambda cls, path, tag: True,
    )
    # not sure whether to monkeypatch of use fixture
    monkeypatch.setattr("shutil.rmtree", lambda path: None)
    assert docker_helper._build_gluubase() is True


def test_setup_container_existing_image(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper._build_gluubase",
        lambda cls: True,
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.image_exists",
        lambda cls, name: [{
            'Created': 1401926735,
            'Id': 'a9eb172552348a9a49180694790b33a1097f546456d041b6e82e4d',
            'ParentId': '120e218dd395ec314e7b6249f39d2853911b3d6def6ea164',
            'RepoTags': ['gluuopendj:latest'],
            'Size': 0,
            'VirtualSize': 2433303,
        }],
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.run_container",
        lambda cls, name, image, port_bindings, volumes, dns, dns_search: "123",
    )

    container_id = docker_helper.setup_container(
        "gluuopendj_123", "gluuopendj",
        "http://example.com/Dockerfile", "127.0.0.1",
    )
    assert container_id == "123"


def test_setup_container_no_gluubase(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper._build_gluubase",
        lambda cls: False,
    )
    container_id = docker_helper.setup_container(
        "gluuopendj_123", "gluuopendj",
        "http://example.com/Dockerfile", "127.0.0.1",
    )
    assert container_id == ""


def test_setup_container_failed(monkeypatch, docker_helper):
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper._build_gluubase",
        lambda cls: True,
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.image_exists",
        lambda cls, name: [],
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.get_remote_files",
        lambda cls, *files: "/tmp/gluuopendj",
    )
    monkeypatch.setattr(
        "gluuapi.helper.docker_helper.DockerHelper.build_image",
        lambda cls, path, tag: False,
    )
    # not sure whether to monkeypatch of use fixture
    monkeypatch.setattr("shutil.rmtree", lambda path: None)

    container_id = docker_helper.setup_container(
        "gluuopendj_123", "gluuopendj",
        "http://example.com/Dockerfile", "127.0.0.1",
    )
    assert container_id == ""


def test_get_remote_files(monkeypatch, docker_helper):
    fake_resp = FakeResp(status_code=200, text="example")
    monkeypatch.setattr("requests.get", lambda url: fake_resp)

    files = ["http://example.com/a.txt"]
    local_dir = docker_helper.get_remote_files(*files)
    file_ = os.path.join(local_dir, "a.txt")

    assert local_dir != ""
    assert os.path.exists(file_)
    assert open(file_).read() == "example"

    # remove temporary dir
    shutil.rmtree(local_dir)


def test_inspect_container(monkeypatch, docker_helper):
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
    assert len(docker_helper.inspect_container("weave"))


def test_init_tls_conn(monkeypatch, provider):
    import tempfile
    from gluuapi.helper import DockerHelper

    _, ca_pem = tempfile.mkstemp(suffix=".pem")
    _, cert_pem = tempfile.mkstemp(suffix=".pem")
    _, key_pem = tempfile.mkstemp(suffix=".pem")

    provider.docker_base_url = "https://127.0.0.1:2375"
    monkeypatch.setattr(
        "gluuapi.model.Provider.ssl_cert_path",
        cert_pem,
    )
    monkeypatch.setattr(
        "gluuapi.model.Provider.ssl_key_path",
        key_pem,
    )
    monkeypatch.setattr(
        "gluuapi.model.Provider.ca_cert_path",
        ca_pem,
    )

    DockerHelper(provider)

    os.unlink(ca_pem)
    os.unlink(cert_pem)
    os.unlink(key_pem)
