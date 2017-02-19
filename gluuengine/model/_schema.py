# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Unicode
from sqlalchemy import Text


CLUSTER_SCHEMA = {
    "name": "clusters",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "name": Unicode(255),
        "description": Unicode(255),
        "ox_cluster_hostname": Unicode(255),
        "org_name": Unicode(255),
        "country_code": Unicode(4),
        "city": Unicode(64),
        "state": Unicode(32),
        "admin_email": Unicode(255),
        "passkey": Unicode(255),
        "admin_pw": Unicode(255),
    }
}


CONTAINER_SCHEMA = {
    "name": "containers",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "container_attrs": JSON,
        "cluster_id": Unicode(36),
        "node_id": Unicode(36),
        "name": Unicode(255),
        "state": Unicode(32),
        "type": Unicode(32),
        "hostname": Unicode(255),
        "cid": Unicode(128),
    }
}


LICENSE_KEY_SCHEMA = {
    "name": "license_keys",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "metadata": JSON,
        "name": Unicode(255),
        "code": Unicode(255),
        "public_key": Text,
        "public_password": Unicode(255),
        "license_password": Unicode(255),
        "signed_license": Text,
        "valid": Boolean,
        "updated_at": BigInteger,
        "passkey": Unicode(255),
    }
}


CONTAINER_LOG_SCHEMA = {
    "name": "container_logs",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "container_name": Unicode(255),
        "state": Unicode(32),
        "setup_log": Unicode(255),
        "teardown_log": Unicode(255),
    }
}


NODE_SCHEMA = {
    "name": "nodes",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "state_attrs": JSON,
        "name": Unicode(255),
        "provider_id": Unicode(36),
        "type": Unicode(32),
    }
}


PROVIDER_SCHEMA = {
    "name": "providers",
    "columns": {
        "id": Unicode(36),
        "_pyobject": Unicode(255),
        "driver_attrs": JSON,
        "name": Unicode(255),
        "driver": Unicode(128),
    }
}

LDAP_SETTING_SCHEMA = {
    "name": "ldap_settings",
    "columns": {
        "id": Unicode(255),
        "_pyobject": Unicode(255),
        "host": Unicode(255),
        "port": Integer,
        "bind_dn": Unicode(255),
        "encoded_bind_password": Unicode(255),
        "encoded_salt": Unicode(255),
        "inum_appliance": Unicode(255),
        "inum_org": Unicode(255),
    }
}
