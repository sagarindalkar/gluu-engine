import os.path
import stat


def test_populate_ssl_cert(provider):
    docker_cert_dir = "/tmp"
    provider.populate({
        "ssl_cert": "ca.pem contents",
        "docker_cert_dir": docker_cert_dir,
    })
    assert oct(os.stat(provider.ssl_cert_path)[stat.ST_MODE])[-3:] == "444"

    # cleanup
    os.chmod(provider.ssl_cert_path, stat.S_IXUSR)
    os.unlink(provider.ssl_cert_path)


def test_populate_ssl_key(provider):
    docker_cert_dir = "/tmp"
    provider.populate({
        "ssl_key": "key.pem contents",
        "docker_cert_dir": docker_cert_dir,
    })
    assert oct(os.stat(provider.ssl_key_path)[stat.ST_MODE])[-3:] == "400"

    # cleanup
    os.chmod(provider.ssl_key_path, stat.S_IXUSR)
    os.unlink(provider.ssl_key_path)


def test_populate_ca_cert(provider):
    docker_cert_dir = "/tmp"
    provider.populate({
        "ca_cert": "ca.pem contents",
        "docker_cert_dir": docker_cert_dir,
    })
    assert oct(os.stat(provider.ca_cert_path)[stat.ST_MODE])[-3:] == "444"

    # cleanup
    os.chmod(provider.ca_cert_path, stat.S_IXUSR)
    os.unlink(provider.ca_cert_path)
