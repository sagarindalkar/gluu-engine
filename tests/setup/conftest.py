import shutil

import pytest


@pytest.fixture()
def ldap_setup(request, ldap_node, cluster):
    from gluuapi.setup import LdapSetup

    setup_obj = LdapSetup(ldap_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxauth_setup(request, oxauth_node, cluster):
    from gluuapi.setup import OxauthSetup

    setup_obj = OxauthSetup(oxauth_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxtrust_setup(request, oxtrust_node, cluster):
    from gluuapi.setup import OxtrustSetup

    setup_obj = OxtrustSetup(oxtrust_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj
