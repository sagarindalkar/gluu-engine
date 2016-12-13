def test_is_in_use(app, db, generic_provider, master_node):
    master_node.provider_id = generic_provider.id
    db.persist(master_node, "nodes")
    assert generic_provider.is_in_use() is True


def test_digitalocean_image(digitalocean_provider):
    assert digitalocean_provider.digitalocean_image == "ubuntu-14-04-x64"
    assert digitalocean_provider.digitalocean_ipv6 is False
