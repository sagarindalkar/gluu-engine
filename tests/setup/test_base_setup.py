import os.path


def test_remove_build_dir(ldap_node, cluster, app):
    from gluuapi.setup.base import BaseSetup

    class FakeSetup(BaseSetup):
        def setup(self):
            pass

    fake_setup = FakeSetup(ldap_node, cluster, app)
    fake_setup.remove_build_dir()

    # ensure ``build_dir`` is deleted
    assert os.path.exists(fake_setup.build_dir) is False


def test_render_template(monkeypatch, ldap_node, cluster, app):
    from gluuapi.setup.base import BaseSetup

    class FakeSetup(BaseSetup):
        def setup(self):
            pass

    monkeypatch.setattr(
        "gluuapi.helper.salt_helper.SaltHelper.copy_file",
        lambda cls, tgt, src, dest: None,
    )

    fake_setup = FakeSetup(ldap_node, cluster, app)
    src = "tests/setup/fake_template.txt"
    dest = os.path.join(fake_setup.build_dir, "fake_template.txt")
    ctx = {"name": "johndoe"}
    fake_setup.render_template(src, dest, ctx)

    assert os.path.exists(dest)
    assert "johndoe" in open(dest, "r").read()
    os.unlink(dest)
