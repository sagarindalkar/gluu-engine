# gluu-flask Cluster Management API Server

## Overview

The gluu-flask server is used to enable management of Gluu Server clusters.
There is an ever-evolving [wiki page](http://www.gluu.co/gluu_salt) which describes
the design of the gluu-flask component.

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

## Configure External Components

`gluu-flask` relies on the following external components:

* weave
* prometheus

Download `postinstall.py` script and run it.

```
wget https://raw.githubusercontent.com/GluuFederation/gluu-cluster-postinstall/master/postinstall.py
python postinstall.py
```

## Run

To run the application in foreground, type the following command in the shell,
and make sure `SALT_MASTER_IPADDR` environment variable is set and
pointed to salt-master IP address.

```
$ source env/bin/activate
$ SALT_MASTER_IPADDR=xxx.xxx.xxx.xxx gluuapi runserver
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
$ SALT_MASTER_IPADDR=xxx.xxx.xxx.xxx gluuapi daemon --pidfile /path/to/pidfile --logfile /path/to/logfile start
```

The daemon has `start`, `stop`, `restart`, and `status` commands.
It's worth noting that `--pidfile` and `--logfile` must be pointed to accessible (writable and readable) path by user who runs the daemon.
By default they are pointed to `/var/run/gluuapi.pid` and `/var/log/gluuapi.log` respectively.

## Testing

Testcases are running using ``pytest`` executed by ``tox``.

```
pip install tox
tox
```

See `tox.ini` for details.
