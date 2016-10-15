# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

'''The app module, containing the app factory function.'''
import os

from crochet import setup as crochet_setup
from flask import Flask

from .settings import ProdConfig
from .settings import DevConfig
from .settings import TestConfig
from .extensions import restapi
from .extensions import ma
from .resource import NodeResource
from .resource import NodeListResource
from .resource import CreateNodeResource
from .resource import ClusterResource
from .resource import ClusterListResource
from .resource import ProviderResource
from .resource import ProviderListResource
from .resource import CreateProviderResource
from .resource import LicenseKeyListResource
from .resource import LicenseKeyResource
from .resource import ContainerLogResource
from .resource import ContainerLogSetupResource
from .resource import ContainerLogTeardownResource
from .resource import ContainerLogListResource
from .resource import ContainerListResource
from .resource import ContainerResource
from .resource import NewContainerResource
from .resource import ScaleContainerResource
from .database import db
from .setup.signals import connect_setup_signals
from .setup.signals import connect_teardown_signals
from .log import configure_global_logging


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
    configure_global_logging()

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

    crochet_setup()
    connect_setup_signals()
    connect_teardown_signals()
    return app


def register_extensions(app):
    restapi.init_app(app)
    db.init_app(app)
    ma.init_app(app)


def register_resources():
    restapi.add_resource(CreateNodeResource,
                         '/nodes/<string:node_type>',
                         endpoint='create_node')
    restapi.add_resource(NodeListResource, '/nodes', endpoint='node_list')
    restapi.add_resource(NodeResource,
                         '/nodes/<string:node_name>',
                         endpoint='node')

    restapi.add_resource(ContainerLogResource,
                         '/container_logs/<id>',
                         endpoint="containerlog",
                         )
    restapi.add_resource(ContainerLogSetupResource,
                         '/container_logs/<id>/setup',
                         endpoint="containerlog_setup",
                         )
    restapi.add_resource(ContainerLogTeardownResource,
                         '/container_logs/<id>/teardown',
                         endpoint="containerlog_teardown",
                         )
    restapi.add_resource(ContainerLogListResource,
                         '/container_logs',
                         endpoint="containerlog_list",
                         )

    restapi.add_resource(ClusterListResource,
                         '/clusters',
                         endpoint="cluster_list",
                         )
    restapi.add_resource(ClusterResource,
                         '/clusters/<string:cluster_id>',
                         endpoint="cluster",
                         )

    restapi.add_resource(ProviderResource,
                         "/providers/<string:provider_id>",
                         endpoint="provider")
    restapi.add_resource(ProviderListResource,
                         "/providers",
                         "/filter-providers/<string:provider_type>",
                         endpoint="provider_list")
    restapi.add_resource(CreateProviderResource,
                         "/providers/<string:provider_type>",
                         endpoint="create_provider")

    restapi.add_resource(LicenseKeyListResource, "/license_keys",
                         endpoint="licensekey_list")
    restapi.add_resource(LicenseKeyResource,
                         "/license_keys/<string:license_key_id>",
                         endpoint="licensekey")

    restapi.add_resource(ContainerListResource,
                         "/containers",
                         "/filter-containers/<string:container_type>",
                         endpoint="container_list",
                         )
    restapi.add_resource(ContainerResource,
                         "/containers/<string:container_id>",
                         endpoint="container",
                         )
    restapi.add_resource(NewContainerResource,
                         "/containers/<string:container_type>",
                         endpoint="new_container",
                         )
    restapi.add_resource(ScaleContainerResource,
                         "/scale-containers/<string:container_type>/<int:number>",
                         endpoint="scale_container",
                         )
