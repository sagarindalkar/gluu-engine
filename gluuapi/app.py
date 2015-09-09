# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

'''The app module, containing the app factory function.'''
import os

from flask import Flask

from gluuapi.settings import ProdConfig
from gluuapi.settings import DevConfig
from gluuapi.settings import TestConfig
from gluuapi.extensions import restapi
from gluuapi.extensions import ma
from gluuapi.resource.node import Node
from gluuapi.resource.node import NodeList
from gluuapi.resource.cluster import Cluster
from gluuapi.resource.cluster import ClusterList
from gluuapi.resource import ProviderResource
from gluuapi.resource import ProviderListResource
from gluuapi.resource import LicenseKeyListResource
from gluuapi.resource import LicenseKeyResource
from gluuapi.database import db


def _get_config_object(api_env=""):
    """Gets config class based on API_ENV environment variable.
    """
    if api_env == "prod":
        config = ProdConfig
    elif api_env == "test":
        config = TestConfig
    else:
        config = DevConfig
    return config


def create_app():
    api_env = os.environ.get("API_ENV")

    app = Flask(__name__)
    app.config.from_object(_get_config_object(api_env))

    # loads custom ``settings.py`` from instance folder
    app.instance_path = app.config["INSTANCE_DIR"]
    app.config.from_pyfile(
        os.path.join(app.instance_path, "settings.py"),
        silent=True,
    )

    register_resources()
    register_extensions(app)
    return app


def register_extensions(app):
    restapi.init_app(app)
    db.init_app(app)
    ma.init_app(app)


def register_resources():
    restapi.add_resource(NodeList, '/nodes')
    restapi.add_resource(Node, '/nodes/<string:node_id>')

    restapi.add_resource(ClusterList, '/clusters')
    restapi.add_resource(Cluster, '/clusters/<string:cluster_id>')

    restapi.add_resource(ProviderResource, "/providers/<string:provider_id>",
                         endpoint="provider")
    restapi.add_resource(ProviderListResource, "/providers",
                         endpoint="providerlist")

    restapi.add_resource(LicenseKeyListResource, "/license_keys",
                         endpoint="licensekeylist")
    restapi.add_resource(LicenseKeyResource,
                         "/license_keys/<string:license_key_id>",
                         endpoint="licensekey")
