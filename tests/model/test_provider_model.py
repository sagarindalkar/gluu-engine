def test_ssl_cert_path(provider):
    provider.docker_cert_dir = "/tmp/docker_certs"
    provider.id = "provider-123"
    assert provider.ssl_cert_path == "/tmp/docker_certs/provider-123__cert.pem"


def test_ssl_key_path(provider):
    provider.docker_cert_dir = "/tmp/docker_certs"
    provider.id = "provider-123"
    assert provider.ssl_key_path == "/tmp/docker_certs/provider-123__key.pem"


def test_ca_cert_path(provider):
    provider.docker_cert_dir = "/tmp/docker_certs"
    provider.id = "provider-123"
    assert provider.ca_cert_path == "/tmp/docker_certs/provider-123__ca.pem"
