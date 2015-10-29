# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os


class Config(object):
    DEBUG = False
    TESTING = False

    # This directory
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PORT = 8080

    DATA_DIR = os.environ.get("DATA_DIR", "/var/lib/gluu-cluster")
    DATABASE_URI = os.path.join(DATA_DIR, "db", "db.json")
    SALT_MASTER_IPADDR = os.environ.get("SALT_MASTER_IPADDR", "")
    TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
    LOG_DIR = os.environ.get("LOG_DIR", "/var/log/gluu")
    INSTANCE_DIR = os.path.join(DATA_DIR, "instance")
    DOCKER_CERT_DIR = os.path.join(DATA_DIR, "docker_certs")
    CUSTOM_LDAP_SCHEMA_DIR = os.path.join(DATA_DIR, "custom", "opendj", "schema")


class ProdConfig(Config):
    """Production configuration.
    """


class DevConfig(Config):
    """Development configuration.
    """
    DEBUG = True
    LOG_DIR = os.environ.get("LOG_DIR", "/var/log/gluu-dev")
    DATA_DIR = os.environ.get("DATA_DIR", "/var/lib/gluu-cluster-dev")
    DATABASE_URI = os.path.join(DATA_DIR, "db", "db_dev.json")
    DOCKER_CERT_DIR = os.path.join(DATA_DIR, "docker_certs")
    INSTANCE_DIR = os.path.join(DATA_DIR, "instance")
    CUSTOM_LDAP_SCHEMA_DIR = os.path.join(DATA_DIR, "custom", "opendj", "schema")


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    DATA_DIR = os.environ.get("DATA_DIR", "/var/lib/gluu-cluster-test")
    DATABASE_URI = os.path.join(DATA_DIR, "db", "db_test.json")
    LOG_DIR = os.environ.get("LOG_DIR", "/var/log/gluu-test")
    DOCKER_CERT_DIR = os.path.join(DATA_DIR, "docker_certs")
    INSTANCE_DIR = os.path.join(DATA_DIR, "instance")
    CUSTOM_LDAP_SCHEMA_DIR = os.path.join(DATA_DIR, "custom", "opendj", "schema")
