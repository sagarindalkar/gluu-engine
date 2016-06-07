# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from collections import defaultdict
import json
import os

import jsonpickle
import tinydb
from werkzeug.utils import import_string
from pymongo import MongoClient


class MongoStorage(tinydb.Storage):
    def __init__(self, uri):
        super(MongoStorage, self).__init__()
        self.uri = uri
        self.dbname = uri.rsplit("/")[-1]
        self._client = None

    @property
    def client(self):
        if not self._client:
            self._client = MongoClient(self.uri)
            self._client.db = self._client[self.dbname]
        return self._client

    def read(self):
        data = defaultdict(dict)

        for collection in self.client.db.collection_names():
            for doc in self.client.db[collection].find():
                data[collection].update({doc["_eid"]: doc})
        return data

    def write(self, data):
        for collection, item in data.iteritems():
            for k, v in item.iteritems():
                v["_eid"] = k
                self.client.db[collection].update({"_id": v["id"]}, v, True)

    def close(self):
        self.client.close()


class MongoTable(tinydb.database.Table):
    def remove(self, cond=None, eids=None):
        def process(data, eid):
            collection = self._storage._table_name
            self._storage._storage.client.db[collection].delete_one({"_eid": eid})
            data.pop(eid)
        self.process_elements(process, cond, eids)


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
            self._db = tinydb.TinyDB(
                self.app.config["DATABASE_URI"],
                storage=MongoStorage,
            )
            self._db.table_class = MongoTable
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

    def export_as_json(self, path):
        data = self.db._storage.read()

        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        with open(path, "w") as fd:
            json.dump(data, fd)
        return path


# shortcut to database object
db = Database()
