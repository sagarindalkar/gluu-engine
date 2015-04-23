import pytest


@pytest.fixture()
def docker_helper(request, app, provider):
    from api.helper.docker_helper import DockerHelper

    helper = DockerHelper(base_url=provider.base_url)

    def teardown():
        helper.docker.close()

    request.addfinalizer(teardown)
    return helper
