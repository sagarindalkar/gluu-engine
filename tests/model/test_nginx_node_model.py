def test_recovery_priority(nginx_node):
    assert nginx_node.recovery_priority == 3
