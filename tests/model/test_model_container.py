def test_ldap_recovery_priority(ldap_container):
    assert ldap_container.recovery_priority == 1


def test_oxauth_recovery_priority(oxauth_container):
    assert oxauth_container.recovery_priority == 2


def test_oxtrust_recovery_priority(oxtrust_container):
    assert oxtrust_container.recovery_priority == 3


def test_oxidp_recovery_priority(oxidp_container):
    assert oxidp_container.recovery_priority == 4


def test_nginx_recovery_priority(nginx_container):
    assert nginx_container.recovery_priority == 5


def test_oxasimba_recovery_priority(oxasimba_container):
    assert oxasimba_container.recovery_priority == 6
