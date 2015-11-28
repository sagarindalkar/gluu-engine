# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import os

import jsonpickle
import tinydb
from werkzeug.utils import import_string


class Database(object):
    def __init__(self, app=None):
        self._db = None
        self.app = app

        if app is not None:
            self.init_app(app)

        # shortcut to ``tinydb.where``
        self.where = tinydb.where

    def init_app(self, app):
        app.config.setdefault("DATABASE_URI", "")
        app.extensions = getattr(app, "extensions", {})
        app.extensions["tinydb"] = self
        self.app = app

    @property
    def db(self):
        assert self.app, "The tinydb extension is not registered in current " \
                         "application. Ensure you have called init_app first."

        if not self._db:
            if not os.path.exists(self.app.config["DATABASE_URI"]):
                try:
                    os.makedirs(
                        os.path.dirname(self.app.config["DATABASE_URI"])
                    )
                except OSError:
                    pass
            self._db = tinydb.TinyDB(self.app.config["DATABASE_URI"])
        return self._db

    def _load_pyobject(self, data):
        # ``jsonpickle.decode`` automatically instantiates object from
        # ``py/object`` value stored in database; the problem is,
        # this object won't recognize new attribute hence we're
        # instantiating object and setting its attributes manually
        cls = import_string(data["py/object"])
        obj = cls()
        for k, v in data.iteritems():
            setattr(obj, k, v)
        return obj

    def get(self, identifier, table_name):
        obj = None
        table = self.db.table(table_name)
        data = table.get(db.where("id") == identifier)

        if data:
            obj = self._load_pyobject(data)
        return obj

    def persist(self, obj, table_name):
        # encode the object so we can decode it later
        encoded = jsonpickle.encode(obj)

        # tinydb requires a ``dict`` object
        data = json.loads(encoded)

        table = self.db.table(table_name)
        table.insert(data)
        return True

    def all(self, table_name):
        table = self.db.table(table_name)
        data = table.all()
        return [self._load_pyobject(item) for item in data]

    def delete(self, identifier, table_name):
        table = self.db.table(table_name)
        table.remove(self.where("id") == identifier)
        return True

    def update(self, identifier, obj, table_name):
        # encode the object so we can decode it later
        encoded = jsonpickle.encode(obj)

        # tinydb requires a ``dict`` object
        data = json.loads(encoded)

        table = self.db.table(table_name)
        table.update(data, self.where("id") == identifier)
        return True

    def search_from_table(self, table_name, condition):
        table = self.db.table(table_name)
        data = table.search(condition)
        return [self._load_pyobject(item) for item in data]

    def count_from_table(self, table_name, condition):
        table = self.db.table(table_name)
        return table.count(condition)

    def update_to_table(self, table_name, condition, obj):
        # encode the object so we can decode it later
        encoded = jsonpickle.encode(obj)

        # tinydb requires a ``dict`` object
        data = json.loads(encoded)

        table = self.db.table(table_name)
        table.update(data, condition)
        return True

    def delete_from_table(self, table_name, condition):
        table = self.db.table(table_name)
        table.remove(condition)


# shortcut to database object
db = Database()
