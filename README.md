# gluu-flask Cluster Management API Server

## Overview

The gluu-flask server is used to enable management of Gluu Server clusters.
There is an ever-evolving [wiki page](http://www.gluu.co/gluu_salt) which describes
the design of the gluu-flask component.

__NOTE__: The `master` branch is used for unreleased version. For __v0.4.x__ releases, use the `version_0.4` branch instead.

## Prerequisites

### Ubuntu packages

```
echo "deb http://repo.gluu.org/ubuntu/ trusty-devel main" | sudo tee /etc/apt/sources.list.d/gluu-repo.list
curl http://repo.gluu.org/ubuntu/gluu-apt.key | sudo apt-key add -
sudo apt-get install -y gluu-master python-pip python-dev swig libsasl2-dev libldap2-dev libssl-dev openjdk-7-jre-headless oxd-license-validator
```

Note: `gluu-master` is a meta package that installs all required packages.

## Deployment

### Install pip and virtualenv

```
wget -q -O- https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | python -
wget -q -O- https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python -
pip install virtualenv
```

### Clone the project

```
$ git clone https://github.com/GluuFederation/gluu-flask.git
$ cd gluu-flask
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python setup.py install
```

## Run

To run the application in foreground, type the following command in the shell:

```
$ source env/bin/activate
$ gluuapi runserver
```

Or, if you have `make` installed

```
$ source env/bin/activate
$ make run
```

## Daemon Mode

To run `gluuapi` in background (daemon mode):

```
$ source env/bin/activate
$ gluuapi daemon --pidfile /path/to/pidfile --logfile /path/to/logfile start
```

The daemon has `start`, `stop`, `restart`, and `status` commands.
It's worth noting that `--pidfile` and `--logfile` must be pointed to accessible (writable and readable) path by user who runs the daemon.
By default they are pointed to `/var/run/gluuapi.pid` and `/var/log/gluuapi.log` respectively.

## Testing

__WARNING__: some testcases are skipped as we need to rewrite the tests to conform to the new codebase.

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.
