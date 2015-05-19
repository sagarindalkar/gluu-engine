# gluu-flask Cluster Management API Server

## Overview

The gluu-flask server is used to enable management of Gluu Server clusters.
There is an ever-evolving [wiki page](http://www.gluu.co/gluu_salt) which describes
the design of the gluu-flask component.

## Prerequisites

### Ubuntu packages

```
sudo apt-get install -y libssl-dev python-dev swig libzmq3-dev
sudo apt-get build-dep openssl
```

### Install docker

Follow these instructions to install the package for Ubuntu Trusty 14.04 managed by docker.com:
[http://docs.docker.com/installation/ubuntulinux](http://docs.docker.com/installation/ubuntulinux/#docker-maintained-package-installation)

For the impatient, just type:

```
curl -sSL https://get.docker.com/ubuntu/ | sudo sh
```

Note: gluu-flask only supports docker v1.5.0 or above.

### Install salt-master

```
echo deb http://ppa.launchpad.net/saltstack/salt/ubuntu `lsb_release -sc` main | sudo tee /etc/apt/sources.list.d/saltstack.list
wget -q -O- "http://keyserver.ubuntu.com:11371/pks/lookup?op=get&search=0x4759FA960E27C0A6" | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y salt-master
```

## Deployment

### Install pip and virtualenv

```
wget -q -O- https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python -
wget -q -O- https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python -
pip install virtualenv
```

### Clone the project

```
git clone https://github.com/GluuFederation/gluu-flask.git
cd gluu-flask
virtualenv env
source env/bin/activate
python setup.py install
```

## Run

To run the application, type the following command in the shell,
and make sure `SALT_MASTER_IPADDR` environment variable is set and
pointed to salt-master IP address.

```
SALT_MASTER_IPADDR=xxx.xxx.xxx.xxx gluuapi
```

## Testing

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.

## Flask Swagger Docs

gluu-flask publishes swagger API documentation. You should be able view this interactive HTML page that lets you play with the API to some extent.

http://localhost:8080/api/spec.html
