# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

import os

from flask_restful import Api
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

restapi = Api(catch_all_404s=True)
ma = Marshmallow()
db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate(
    db=db,
    directory=os.path.join(os.path.dirname(__file__), "migrations"),
)
