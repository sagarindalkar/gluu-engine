# Gluu Server Docker Edition REST API

## Overview

The gluu-engine (formerly gluu-flask) server is used to enable management of Gluu Server Docker Editiion clusters.
There is an ever-evolving [wiki page](http://www.gluu.co/gluu_salt) which describes
the design of the gluu-engine component.

__NOTE__: The `master` branch is used for unreleased version. For __v0.4.x__ releases, use the `version_0.4` branch instead.

## Prerequisites

### Ubuntu packages

```
echo "deb http://repo.gluu.org/ubuntu/ trusty-devel main" | sudo tee /etc/apt/sources.list.d/gluu-repo.list
curl http://repo.gluu.org/ubuntu/gluu-apt.key | sudo apt-key add -
sudo apt-get install -y python-pip python-dev swig libsasl2-dev libssl-dev openjdk-7-jre-headless oxd-license-validator
```

### Docker Engine

```
apt-get update
apt-get install apt-transport-https ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-engine=1.11.2-0~trusty
```

### Docker Machine

```
$ curl -L https://github.com/docker/machine/releases/download/v0.7.0/docker-machine-`uname -s`-`uname -m` > /usr/local/bin/docker-machine \
    && chmod +x /usr/local/bin/docker-machine
```

## Deployment

### Clone the project

```
$ git clone https://github.com/GluuFederation/gluu-engine.git
$ cd gluu-engine
$ virtualenv env
$ source env/bin/activate
$ pip install -U pip
$ pip install -r requirements.txt
$ python setup.py install
```

## Run

For development mode:

```
$ source env/bin/activate
$ gunicorn -b 127.0.0.1:8080 --log-level info --access-logfile - --error-logfile - --reload
```

For production mode:

```
$ source env/bin/activate
$ gunicorn -b 127.0.0.1:8080 --log-level warning --access-logfile - --error-logfile - -e API_ENV=prod
```

## Testing

__WARNING__: some testcases are skipped as we need to rewrite the tests to conform to the new codebase.

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.
