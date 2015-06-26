# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os


class Config(object):
    DEBUG = False
    TESTING = False

    # This directory
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PORT = 8080
    DATA_DIR = os.environ.get(
        "DATA_DIR",
        os.path.expanduser('~') + '/.gluu-cluster',
    )
    DATABASE_URI = os.path.join(DATA_DIR, "db", "db.json")
    SALT_MASTER_IPADDR = os.environ.get("SALT_MASTER_IPADDR", "")
    TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
    LOG_DIR = os.environ.get("LOG_DIR", "/var/log/gluu")
    INSTANCE_DIR = os.path.join(DATA_DIR, "instance")
    DOCKER_CERT_DIR = os.path.join(DATA_DIR, "docker_certs")


class ProdConfig(Config):
    """Production configuration.
    """


class DevConfig(Config):
    """Development configuration.
    """
    DEBUG = True
    DATABASE_URI = os.path.join(Config.DATA_DIR, "db", "db_dev.json")
    LOG_DIR = os.environ.get("LOG_DIR", "/tmp/gluu-dev")


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    DATABASE_URI = os.path.join(Config.DATA_DIR, "db", "db_test.json")
    LOG_DIR = os.environ.get("LOG_DIR", "/tmp/gluu-test")
