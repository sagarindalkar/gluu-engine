def test_recovery_priority(ldap_node):
    assert ldap_node.recovery_priority == 1
