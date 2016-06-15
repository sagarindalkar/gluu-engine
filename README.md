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

Follow the guide to install Docker Engine here: https://docs.docker.com/engine/installation/linux/ubuntulinux/.

### Docker Machine

Follow the guide to install Docker Machine here: https://docs.docker.com/machine/install-machine/

## Deployment

### Install pip and virtualenv

```
wget -q -O- https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python -
wget -q -O- https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python -
pip install virtualenv
```

### Clone the project

```
$ git clone https://github.com/GluuFederation/gluu-engine.git
$ cd gluu-engine
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python setup.py install
```

## Run

To run the application in foreground, type the following command in the shell:

```
$ source env/bin/activate
$ gluuengine runserver  # good for development
```

For production mode, we can use `gunicorn`:

```
$ gunicorn -b 127.0.0.1:8080 --log-level warning --access-logfile - --error-logfile -
```

## Testing

__WARNING__: some testcases are skipped as we need to rewrite the tests to conform to the new codebase.

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.
