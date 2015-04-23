import os.path
import shutil


def test_write_ldap_pw(ldap_node, cluster):
    from api.setup.ldap_setup import ldapSetup

    setup_obj = ldapSetup(ldap_node, cluster)
    setup_obj.write_ldap_pw()

    pw_file = os.path.join(setup_obj.build_dir, ".pw")

    assert os.path.exists(pw_file) is True
    assert cluster.decrypted_admin_pw in open(pw_file, "r").read()
    shutil.rmtree(setup_obj.build_dir)


def test_add_ldap_schema(ldap_node, cluster):
    from api.setup.ldap_setup import ldapSetup

    setup_obj = ldapSetup(ldap_node, cluster)
    setup_obj.add_ldap_schema()

    for schema in ldap_node.schemaFiles:
        schema_file = os.path.join(setup_obj.build_dir,
                                   os.path.basename(schema))
        assert os.path.exists(schema_file) is True
        # assert cluster.inumOrgFN in open(schema_file, "r").read()
