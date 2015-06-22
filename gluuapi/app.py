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
from gluuapi.resource import LicenseResource
from gluuapi.resource import LicenseListResource
from gluuapi.resource import LicenseCredentialListResource
from gluuapi.resource import LicenseCredentialResource
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
    restapi.add_resource(NodeList, '/node')
    restapi.add_resource(Node, '/node/<string:node_id>')

    restapi.add_resource(ClusterList, '/cluster')
    restapi.add_resource(Cluster, '/cluster/<string:cluster_id>')

    restapi.add_resource(ProviderResource, "/provider/<string:provider_id>",
                         endpoint="provider")
    restapi.add_resource(ProviderListResource, "/provider",
                         endpoint="providerlist")

    restapi.add_resource(LicenseResource, "/license/<string:license_id>",
                         endpoint="license")
    restapi.add_resource(LicenseListResource, "/license",
                         endpoint="licenselist")

    restapi.add_resource(LicenseCredentialListResource, "/license_credential",
                         endpoint="licensecredlist")
    restapi.add_resource(LicenseCredentialResource, "/license_credential/<string:credential_id>",
                         endpoint="licensecred")
