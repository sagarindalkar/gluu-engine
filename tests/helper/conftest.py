import pytest


@pytest.fixture()
def docker_helper(request, app, provider):
    from gluuapi.helper.docker_helper import DockerHelper

    helper = DockerHelper(base_url=provider.docker_base_url)

    def teardown():
        helper.docker.close()

    request.addfinalizer(teardown)
    return helper


@pytest.fixture(scope="session")
def salt_helper():
    from gluuapi.helper.salt_helper import SaltHelper

    helper = SaltHelper()
    return helper
