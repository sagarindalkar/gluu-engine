import os.path


def test_remove_build_dir(base_setup):
    base_setup.remove_build_dir()

    # ensure ``build_dir`` is deleted
    assert os.path.exists(base_setup.build_dir) is False


def test_render_template(patched_po_run, base_setup):
    src = "tests/setup/fake_template.txt"
    dest = os.path.join(base_setup.build_dir, "fake_template.txt")
    ctx = {"name": "johndoe"}
    base_setup.render_template(src, dest, ctx)

    assert os.path.exists(dest)
    assert "johndoe" in open(dest, "r").read()
    os.unlink(dest)


def test_gen_cert(base_setup, patched_exec_cmd):
    base_setup.gen_cert("ldap", "secret", "root", "root", "localhost")


def test_change_cert_access(base_setup, patched_exec_cmd):
    base_setup.change_cert_access("root", "root")


def test_get_template_path(app, base_setup):
    import os

    expected = os.path.join(app.config["TEMPLATES_DIR"], "random/unique.txt")
    assert base_setup.get_template_path("random/unique.txt") == expected


def test_render_jinja_template(base_setup):
    import os
    from jinja2 import Environment
    from jinja2 import FileSystemLoader

    base_setup.jinja_env = Environment(
        loader=FileSystemLoader(os.path.dirname(__file__))
    )
    src = "fake_jinja_template.txt"
    ctx = {"name": "johndoe"}
    txt = base_setup.render_jinja_template(src, ctx)
    assert "johndoe" in txt


def test_copy_rendered_jinja_template(base_setup, patched_po_run):
    import os
    from jinja2 import Environment
    from jinja2 import FileSystemLoader

    base_setup.jinja_env = Environment(
        loader=FileSystemLoader(os.path.dirname(__file__))
    )
    src = "fake_jinja_template.txt"
    ctx = {"name": "johndoe"}
    dest = os.path.join(base_setup.build_dir, "fake_jinja_template.txt")
    base_setup.copy_rendered_jinja_template(src, dest, ctx)


def test_reload_supervisor(base_setup, patched_exec_cmd, patched_sleep):
    base_setup.reload_supervisor()


def test_ldap_failover_hostname(monkeypatch, base_setup):
    monkeypatch.setattr(
        "gluuapi.weave.Weave.dns_args",
        lambda cls: ("", "weave.local",),
    )
    assert base_setup.ldap_failover_hostname() == "ldap.weave.local"


def test_write_salt_file(ox_setup, patched_po_run):
    ox_setup.write_salt_file()


def test_gen_keystore(ox_setup, patched_po_run, patched_exec_cmd):
    ox_setup.gen_keystore("shibIDP", "/tmp/shibIDP.jks", "changeme",
                          "in.key", "in.crt", "root", "root", "localhost")


def test_render_ldap_props_template(monkeypatch, ox_setup, patched_po_run):
    monkeypatch.setattr(
        "gluuapi.setup.base.OxSetup.ldap_failover_hostname",
        lambda cls: "ldap.weave.local",
    )
    ox_setup.render_ldap_props_template()


def test_configure_vhost(ox_setup, patched_exec_cmd):
    ox_setup.configure_vhost()


def test_import_nginx_cert(ox_setup, patched_po_run, patched_exec_cmd):
    ox_setup.import_nginx_cert()
