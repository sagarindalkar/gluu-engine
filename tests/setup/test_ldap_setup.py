import os.path
import shutil


def test_write_ldap_pw(monkeypatch, ldap_node, cluster):
    from api.setup.ldap_setup import ldapSetup

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    monkeypatch.setattr(
        "api.helper.salt_helper.SaltHelper.copy_file",
        lambda cls, tgt, src, dest: None,
    )

    setup_obj = ldapSetup(ldap_node, cluster)
    setup_obj.write_ldap_pw()

    pw_file = os.path.join(setup_obj.build_dir, ".pw")

    assert os.path.exists(pw_file) is True
    assert cluster.decrypted_admin_pw in open(pw_file, "r").read()
    shutil.rmtree(setup_obj.build_dir)


def test_add_ldap_schema(monkeypatch, ldap_node, cluster):
    from api.setup.ldap_setup import ldapSetup

    monkeypatch.setattr(
        "salt.client.LocalClient.cmd",
        lambda cls, tgt, fun, arg: None,
    )

    monkeypatch.setattr(
        "api.helper.salt_helper.SaltHelper.copy_file",
        lambda cls, tgt, src, dest: None,
    )

    setup_obj = ldapSetup(ldap_node, cluster)
    setup_obj.add_ldap_schema()

    for schema in ldap_node.schemaFiles:
        schema_file = os.path.join(setup_obj.build_dir,
                                   os.path.basename(schema))
        assert os.path.exists(schema_file) is True
    shutil.rmtree(setup_obj.build_dir)
