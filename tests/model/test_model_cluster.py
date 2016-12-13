def test_cluster_as_dict():
    from gluuengine.model import Cluster

    cluster = Cluster()
    actual = cluster.as_dict()

    for field in cluster.resource_fields.keys():
        assert field in actual


def test_decrypted_admin_pw():
    from gluuengine.model import Cluster
    from gluuengine.utils import generate_passkey
    from gluuengine.utils import encrypt_text

    passkey = generate_passkey()
    admin_pw = encrypt_text("secret", passkey)
    cluster = Cluster({"admin_pw": admin_pw, "passkey": passkey})
    assert cluster.decrypted_admin_pw == "secret"


def test_get_containers(app, db, cluster, ldap_container):
    db.persist(ldap_container, "containers")
    data = cluster.get_containers(state=None)

    for item in data:
        assert item.cluster_id == cluster.id


def test_get_containers_by_state(app, db, cluster, ldap_container):
    db.persist(cluster, "clusters")
    ldap_container.state = "FAILED"
    db.persist(ldap_container, "containers")
    assert cluster.get_containers(type_="ldap", state="FAILED")


def test_count_containers(app, db, cluster, ldap_container):
    db.persist(ldap_container, "containers")
    assert cluster.count_containers(state=None) == 1


def test_count_containers_by_state(app, db, cluster, ldap_container):
    db.persist(cluster, "clusters")
    ldap_container.state = "FAILED"
    db.persist(ldap_container, "containers")
    assert cluster.count_containers(type_="ldap", state="FAILED") == 1
