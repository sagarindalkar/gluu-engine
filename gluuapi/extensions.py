# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""
from flask_restful import Api
from flask_marshmallow import Marshmallow

restapi = Api(catch_all_404s=True)
ma = Marshmallow()
