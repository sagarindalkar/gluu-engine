# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

'''The app module, containing the app factory function.'''
import os

from flask import Flask

from .settings import ProdConfig
from .settings import DevConfig
from .settings import TestConfig
from .extensions import restapi
from .extensions import ma
from .resource import NodeResource
from .resource import NodeListResource
from .resource import ClusterResource
from .resource import ClusterListResource
from .resource import ProviderResource
from .resource import ProviderListResource
from .resource import CreateProviderResource
from .resource import LicenseKeyListResource
from .resource import LicenseKeyResource
from .resource import NodeLogResource
from .resource import NodeLogSetupResource
from .resource import NodeLogTeardownResource
from .resource import NodeLogListResource
from .database import db


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
    # to enable weave encryption put WEAVE_ENCRYPTION = True
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
    restapi.add_resource(NodeListResource, '/nodes')
    restapi.add_resource(NodeResource, '/nodes/<string:node_id>')

    restapi.add_resource(NodeLogResource, '/node_logs/<id>')
    restapi.add_resource(NodeLogSetupResource, '/node_logs/<id>/setup')
    restapi.add_resource(NodeLogTeardownResource, '/node_logs/<id>/teardown')
    restapi.add_resource(NodeLogListResource, '/node_logs')

    restapi.add_resource(ClusterListResource, '/clusters')
    restapi.add_resource(ClusterResource, '/clusters/<string:cluster_id>')

    #restapi.add_resource(ProviderResource, "/providers/<string:provider_id>",
    #                     endpoint="provider")
    #restapi.add_resource(ProviderListResource, "/providers",
    #                     endpoint="providerlist")
    restapi.add_resource(ProviderResource,
        "/providers/<string:provider_type>/<string:provider_id>",
        endpoint="provider")
    restapi.add_resource(ProviderListResource,
        "/providers/<string:provider_type>",
        endpoint="provider_list")
    restapi.add_resource(CreateProviderResource,
        "/providers/<string:provider_type>",
        endpoint="Create_Provider")

    restapi.add_resource(LicenseKeyListResource, "/license_keys",
                         endpoint="licensekeylist")
    restapi.add_resource(LicenseKeyResource,
                         "/license_keys/<string:license_key_id>",
                         endpoint="licensekey")
