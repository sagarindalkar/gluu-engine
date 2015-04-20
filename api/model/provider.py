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
import uuid

from flask_restful_swagger import swagger
from flask.ext.restful import fields

from api.model.base import BaseModel


@swagger.model
class Provider(BaseModel):
    """Provider is a model represents a Docker host.

    Docker host could be any reachable machine, either local or remote.
    """
    resource_fields = {
        "id": fields.String(attribute="Provider unique identifier"),
        "base_url": fields.String(
            attribute="URL to Docker API, could be unix socket or tcp",
        ),
        "name": fields.String(attribute="Provider name"),
    }

    def __init__(self, fields=None):
        fields = fields or {}

        self.id = str(uuid.uuid4())
        self.base_url = fields.get("base_url", "")
        self.name = fields.get("name", "")
