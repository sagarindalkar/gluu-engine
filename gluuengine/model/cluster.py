# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from .base import STATE_SUCCESS
from .container import Container
from ..database import db
from ..utils import decrypt_text


class Cluster(db.Model):
    __tablename__ = "clusters"

    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    name = db.Column(db.Unicode(255))
    description = db.Column(db.Unicode(255))
    ox_cluster_hostname = db.Column(db.Unicode(255))
    org_name = db.Column(db.Unicode(128))
    country_code = db.Column(db.Unicode(2))
    city = db.Column(db.Unicode(64))
    state = db.Column(db.Unicode(64))
    admin_email = db.Column(db.Unicode(255))
    passkey = db.Column(db.Unicode(255))
    admin_pw = db.Column(db.Unicode(255))

    @property
    def decrypted_admin_pw(self):
        """Gets decrypted admin password.
        """
        return decrypt_text(self.admin_pw, self.passkey)

    @property
    def shib_jks_fn(self):
        return "/etc/certs/shibIDP.jks"

    @property
    def scim_rp_client_jks_fn(self):
        return "/etc/certs/scim-rp.jks"

    @property
    def scim_rs_client_jks_fn(self):
        return "/etc/certs/scim-rs.jks"

    @property
    def oxauth_openid_jks_fn(self):
        return "/etc/certs/oxauth-keys.jks"

    @property
    def asimba_jks_fn(self):
        return "/etc/certs/asimbaIDP.jks"

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ox_cluster_hostname': self.ox_cluster_hostname,
            'org_name': self.org_name,
            'country_code': self.country_code,
            'city': self.city,
            'state': self.state,
            'admin_email': self.admin_email,
        }

    def count_containers(self, type_="", state=STATE_SUCCESS):
        """Counts available containers objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A counter of how many container objects related to the cluster.
        """
        condition = {"cluster_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return Container.query.filter_by(**condition).count()

    def get_containers(self, type_="", state=STATE_SUCCESS):
        """Gets available container objects (models).

        :param state: State of the container (one of SUCCESS, DISABLED,
                      FAILED, IN_PROGRESS).
        :param type_: Type of the container.
        :returns: A list of container objects.
        """
        condition = {"cluster_id": self.id}
        if state:
            condition["state"] = state
        if type_:
            condition["type"] = type_
        return Container.query.filter_by(**condition).all()

    def as_dict(self):
        return self.resource_fields
