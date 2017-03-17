import pytest


@pytest.mark.skip(reason="rewrite needed")
def test_setup(oxauth_setup, cluster, db, patched_sleep,
               patched_exec_cmd, patched_run):
    db.persist(cluster, "clusters")
    # TODO: it might be better to split the tests
    oxauth_setup.setup()


@pytest.mark.skip(reason="rewrite needed")
def test_teardown(oxauth_setup, patched_exec_cmd):
    oxauth_setup.teardown()
