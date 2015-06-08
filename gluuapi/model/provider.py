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

from gluuapi.database import db
from gluuapi.model.base import BaseModel


@swagger.model
class Provider(BaseModel):
    """Provider is a model represents a Docker host.

    Docker host could be any reachable machine, either local or remote.
    """
    resource_fields = {
        "id": fields.String,
        "docker_base_url": fields.String,
        "hostname": fields.String,
        "license_id": fields.String,
    }

    def __init__(self, fields=None):
        self.id = str(uuid.uuid4())
        self.populate(fields)

    @property
    def type(self):
        return "master" if not self.license_id else "consumer"

    @property
    def nodes_count(self):
        condition = db.where("provider_id") == self.id
        return db.count_from_table("nodes", condition)

    def get_node_objects(self, type_=""):
        condition = db.where("provider_id") == self.id
        if type_:
            condition = (condition) & (db.where("type") == type_)
        return db.search_from_table("nodes", condition)

    def populate(self, fields=None):
        fields = fields or {}

        self.docker_base_url = fields.get("docker_base_url", "")
        self.hostname = fields.get("hostname", "")

        # A reference to ``gluuapi.models.license.License.id``.
        # If the value this attribute is set, provider is considered
        # as ``consumer``; otherwise ``master`` is the role of
        # this provider as default.
        self.license_id = fields.get("license_id", "")
