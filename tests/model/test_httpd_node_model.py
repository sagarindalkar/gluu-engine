def test_recovery_priority(httpd_node):
    assert httpd_node.recovery_priority == 3
