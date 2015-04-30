# -*- coding: utf-8 -*-
'''The app module, containing the app factory function.'''
from flask import Flask

from gluuapi.settings import ProdConfig
from gluuapi.extensions import (
    restapi,
)
from gluuapi.resource.node import Node
from gluuapi.resource.node import NodeList
from gluuapi.resource.cluster import Cluster
from gluuapi.resource.cluster import ClusterList
from gluuapi.resource import ProviderResource
from gluuapi.resource import ProviderListResource
from gluuapi.database import db


def create_app(config_object=ProdConfig):
    '''An application factory, as explained here:
        http://flask.pocoo.org/docs/patterns/appfactories/

    :param config_object: The configuration object to use.
    '''
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_resources()
    register_extensions(app)
    return app


def register_extensions(app):
    restapi.init_app(app)
    db.init_app(app)


def register_resources():
    restapi.add_resource(NodeList, '/node')
    restapi.add_resource(Node, '/node/<string:node_id>')
    restapi.add_resource(ClusterList, '/cluster')
    restapi.add_resource(Cluster, '/cluster/<string:cluster_id>')
    restapi.add_resource(ProviderResource, "/provider/<string:provider_id>", endpoint="provider")
    restapi.add_resource(ProviderListResource, "/provider", endpoint="providerlist")
