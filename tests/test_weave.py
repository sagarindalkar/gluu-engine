import pytest


def test_weave_dns_add(monkeypatch, app, master_node):
    from gluuengine.weave import Weave

    monkeypatch.setattr(
        "gluuengine.machine.Machine.ssh",
        lambda cls, name, cmd: "",
    )

    weave = Weave(master_node, app)
    weave.dns_add("random-id", "ldap.weave.local")


def test_weave_docker_bridge_ip(monkeypatch, app, master_node):
    from gluuengine.weave import Weave

    bridge_ip = "172.42.0.1"
    monkeypatch.setattr(
        "gluuengine.machine.Machine.ssh",
        lambda cls, name, cmd: bridge_ip,
    )

    weave = Weave(master_node, app)
    assert weave.docker_bridge_ip() == bridge_ip


@pytest.mark.parametrize("separator", [
    " ",
    "=",
])
def test_weave_dns_args(monkeypatch, app, master_node, separator):
    from gluuengine.weave import Weave

    dns_args = "--dns{}10.10.0.1 --dns-search=weave.local.".format(separator)
    monkeypatch.setattr(
        "gluuengine.machine.Machine.ssh",
        lambda cls, name, cmd: dns_args,
    )

    weave = Weave(master_node, app)
    _dns, _dns_search = weave.dns_args()
    assert _dns == "10.10.0.1"
    assert _dns_search == "weave.local."
