# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""
from flask_restful import Api
from flask_restful_swagger import swagger
from flask_marshmallow import Marshmallow

restapi = swagger.docs(
    Api(catch_all_404s=True),
    apiVersion='0.2.0',
    api_spec_url='/api/spec',
    description='gluu cluster API',
)
ma = Marshmallow()
