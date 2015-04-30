import shutil

import pytest


@pytest.fixture()
def ldap_setup(request, ldap_node, cluster):
    from gluuapi.setup.ldap_setup import ldapSetup

    setup_obj = ldapSetup(ldap_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxauth_setup(request, oxauth_node, cluster):
    from gluuapi.setup.ldap_setup import OxAuthSetup

    setup_obj = OxAuthSetup(oxauth_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj


@pytest.fixture()
def oxtrust_setup(request, oxtrust_node, cluster):
    from gluuapi.setup.oxtrust_setup import OxTrustSetup

    setup_obj = OxTrustSetup(oxtrust_node, cluster)

    def teardown():
        shutil.rmtree(setup_obj.build_dir)

    request.addfinalizer(teardown)
    return setup_obj
