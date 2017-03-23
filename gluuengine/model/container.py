# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from sqlalchemy import JSON

from ..extensions import db


class Container(db.Model):
    __tablename__ = "containers"

    id = db.Column(db.Unicode(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    cluster_id = db.Column(db.Unicode(36))
    node_id = db.Column(db.Unicode(36))
    container_attrs = db.Column(JSON)
    name = db.Column(db.Unicode(255))
    state = db.Column(db.Unicode(32))
    type = db.Column(db.Unicode(32))
    hostname = db.Column(db.Unicode(255))
    cid = db.Column(db.Unicode(128))

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "container",
    }

    @property
    def image(self):
        """Container image. Must be overriden in subclass.
        """
        raise NotImplemented("image for the container must be defined")

    @property
    def resource_fields(self):
        return {
            'id': self.id,
            'type': self.type,
            'cluster_id': self.cluster_id,
            'node_id': self.node_id,
            "name": self.name,
            "state": self.state,
            "hostname": self.hostname,
            "cid": self.cid,
        }

    def as_dict(self):
        return self.resource_fields


class OxauthContainer(Container):
    # __table_args__ = {'extend_existing': True}

    __mapper_args__ = {
        "polymorphic_identity": "oxauth",
    }

    @property
    def cert_folder(self):
        return self.container_attrs["cert_folder"]

    @property
    def image(self):
        return "oxauth"

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


@db.event.listens_for(OxauthContainer, "init")
def receive_init_oxauth(target, args, kwargs):
    target.container_attrs = {
        "ldap_binddn": "cn=directory manager,o=gluu",
        "cert_folder": "/etc/certs",
        "oxauth_lib": "/opt/gluu/jetty/oxauth/webapps/oxauth/WEB-INF/lib",
        "conf_dir": "/etc/gluu/conf",
    }


class OxtrustContainer(Container):
    __mapper_args__ = {
        "polymorphic_identity": "oxtrust",
    }

    @property
    def cert_folder(self):
        return self.container_attrs["cert_folder"]

    @property
    def image(self):
        return "oxtrust"

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


@db.event.listens_for(OxtrustContainer, "init")
def receive_init_oxtrust(target, args, kwargs):
    target.container_attrs = {
        "cert_folder": "/etc/certs",
        "ldap_binddn": "cn=directory manager,o=gluu",
        "conf_dir": "/etc/gluu/conf",
    }


class OxidpContainer(Container):
    __mapper_args__ = {
        "polymorphic_identity": "oxidp",
    }

    @property
    def image(self):
        return "oxidp"

    @property
    def cert_folder(self):
        return self.container_attrs["cert_folder"]

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


@db.event.listens_for(OxidpContainer, "init")
def receive_init_oxidp(target, args, kwargs):
    target.container_attrs = {
        "cert_folder": "/etc/certs",
        "ldap_binddn": "cn=directory manager,o=gluu",
        "conf_dir": "/etc/gluu/conf",
        "saml_type": "shibboleth",
    }


class NginxContainer(Container):
    __mapper_args__ = {
        "polymorphic_identity": "nginx",
    }

    @property
    def image(self):
        return "nginx"

    @property
    def cert_folder(self):
        return self.container_attrs["cert_folder"]


@db.event.listens_for(NginxContainer, "init")
def receive_init_nginx(target, args, kwargs):
    target.container_attrs = {
        "cert_folder": "/etc/certs",
    }


class OxasimbaContainer(Container):
    __mapper_args__ = {
        "polymorphic_identity": "oxasimba",
    }

    @property
    def image(self):
        return "oxasimba"

    @property
    def cert_folder(self):
        return self.container_attrs["cert_folder"]

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


@db.event.listens_for(OxasimbaContainer, "init")
def receive_init_oxasimba(target, args, kwargs):
    target.container_attrs = {
        "cert_folder": "/etc/certs",
        "ldap_binddn": "cn=directory manager,o=gluu",
        "conf_dir": "/etc/gluu/conf",
    }


class OxelevenContainer(Container):
    __mapper_args__ = {
        "polymorphic_identity": "oxeleven",
    }

    @property
    def image(self):
        return "oxeleven"
