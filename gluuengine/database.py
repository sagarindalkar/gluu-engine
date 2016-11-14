# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import inspect

from werkzeug.utils import import_string
from flask_pymongo import PyMongo
from flask_dataset import Dataset


def _load_pyobject(data):
    # FIXME: "py/object" sometime is not recognized
    if "_pyobject" in data:
        imp_path = data["_pyobject"]
    else:
        imp_path = data["py/object"]

    cls = import_string(imp_path)
    obj = cls(data)
    return obj


def get_model_path(model):
    return ".".join([inspect.getmodule(model).__name__,
                     model.__class__.__name__])


class Database(object):
    def __init__(self, app=None):
        self._backend = None
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    @property
    def backend(self):
        if not self._backend:
            db_uri = self.app.config["DATABASE_URI"]
            if db_uri.startswith("mongodb"):
                # flask-pymongo compatibility
                self.app.config["MONGO_URI"] = db_uri
                self._backend = PyMongoBackend(self.app)
            else:
                # flask-dataset compatibility
                self.app.config["DATASET_DATABASE_URI"] = db_uri
                self._backend = DatasetBackend(self.app)
        return self._backend

    def get(self, identifier, table_name):
        return self.backend.get(identifier, table_name)

    def persist(self, obj, table_name, **kwargs):
        return self.backend.persist(obj, table_name, **kwargs)

    def all(self, table_name):
        return self.backend.all(table_name)

    def delete(self, identifier, table_name):
        return self.backend.delete(identifier, table_name)

    def update(self, identifier, obj, table_name, **kwargs):
        return self.backend.update(identifier, obj, table_name, **kwargs)

    def search_from_table(self, table_name, condition):
        return self.backend.search_from_table(table_name, condition)

    def count_from_table(self, table_name, condition):
        return self.backend.count_from_table(table_name, condition)

    def update_to_table(self, table_name, condition, obj, **kwargs):
        return self.backend.update_to_table(table_name, condition, obj, **kwargs)

    def delete_from_table(self, table_name, condition):
        return self.backend.delete_from_table(table_name, condition)


class PyMongoBackend(PyMongo):
    def get(self, identifier, table_name):
        obj = self.db[table_name].find_one({"id": identifier})

        if not obj:
            return
        return _load_pyobject(obj)

    def persist(self, obj, table_name, **kwargs):
        data = obj.to_primitive()
        data["_id"] = data["id"]
        data["_pyobject"] = get_model_path(obj)
        return self.db[table_name].insert_one(data)

    def all(self, table_name):
        data = self.db[table_name].find()
        return [_load_pyobject(item) for item in data]

    def delete(self, identifier, table_name):
        return self.db[table_name].delete_one({"id": identifier})

    def update(self, identifier, obj, table_name, **kwargs):
        data = obj.to_primitive()
        data["_pyobject"] = get_model_path(obj)
        return self.db[table_name].update({"id": identifier}, data, True)

    def search_from_table(self, table_name, condition):
        data = self.db[table_name].find(condition)
        return [_load_pyobject(item) for item in data]

    def count_from_table(self, table_name, condition):
        return self.db[table_name].count(condition)

    def update_to_table(self, table_name, condition, obj, **kwargs):
        data = obj.to_primitive()
        data["_pyobject"] = get_model_path(obj)
        return self.db[table_name].update(condition, data, True)

    def delete_from_table(self, table_name, condition):
        return self.db[table_name].delete_one(condition)


class DatasetBackend(Dataset):
    def _get_table(self, table_name):
        return self.connection.get_table(table_name, primary_id="id",
                                         primary_type="String(36)")

    def get(self, identifier, table_name):
        obj = self._get_table(table_name).find_one(id=identifier)

        if not obj:
            return
        return _load_pyobject(obj)

    def persist(self, obj, table_name, **kwargs):
        with self.app.test_request_context():
            data = obj.to_primitive()
            data["_pyobject"] = get_model_path(obj)
            return self._get_table(table_name).insert(
                data,
                ensure=True,
                types=kwargs.get("types", {}),
            )

    def all(self, table_name):
        with self.app.test_request_context():
            table = self._get_table(table_name)
            return [_load_pyobject(item) for item in table.all()]

    def delete(self, identifier, table_name):
        with self.app.test_request_context():
            return self._get_table(table_name).delete(id=identifier)

    def update(self, identifier, obj, table_name, **kwargs):
        with self.app.test_request_context():
            data = obj.to_primitive()
            data["_pyobject"] = get_model_path(obj)
            return self._get_table(table_name).update(
                {"id": identifier},
                data,
                ensure=True,
                types=kwargs.get("types", {}),
            )

    def search_from_table(self, table_name, condition):
        with self.app.test_request_context():
            data = self._get_table(table_name).find(**condition)
            return [_load_pyobject(item) for item in data]

    def count_from_table(self, table_name, condition):
        with self.app.test_request_context():
            return self._get_table(table_name).count(**condition)

    def update_to_table(self, table_name, condition, obj, **kwargs):
        with self.app.test_request_context():
            data = obj.to_primitive()
            data["_pyobject"] = get_model_path(obj)
            return self._get_table(table_name).update(
                condition,
                data,
                ensure=True,
                types=kwargs.get("types", {}),
            )

    def delete_from_table(self, table_name, condition):
        with self.app.test_request_context():
            return self._get_table(table_name).delete(**condition)


# shortcut to database object
db = Database()
