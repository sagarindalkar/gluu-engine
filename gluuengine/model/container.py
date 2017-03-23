# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from schematics.types import StringType
from schematics.types.compound import PolyModelType

from ._schema import CONTAINER_SCHEMA
from .base import BaseModel


class Container(BaseModel):
    @property
    def _schema(self):
        return CONTAINER_SCHEMA

    def _resolve_container_attr(self, field):
        try:
            return self.container_attrs.get(field)
        except (AttributeError, TypeError,):
            return self._initial.get(field)

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


class OxauthContainer(Container):
    class ContainerAttrs(BaseModel):
        ldap_binddn = StringType(default='cn=directory manager,o=gluu')
        cert_folder = StringType(default="/etc/certs")
        oxauth_lib = StringType(default="/opt/gluu/jetty/oxauth/webapps/oxauth/WEB-INF/lib")
        conf_dir = StringType(default="/etc/gluu/conf")

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="oxauth")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def image(self):
        return "oxauth"

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


class OxtrustContainer(Container):
    class ContainerAttrs(BaseModel):
        ldap_binddn = StringType(default='cn=directory manager,o=gluu')
        cert_folder = StringType(default="/etc/certs")
        conf_dir = StringType(default="/etc/gluu/conf")

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="oxtrust")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def image(self):
        return "oxtrust"

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


class OxidpContainer(Container):
    class ContainerAttrs(BaseModel):
        ldap_binddn = StringType(default='cn=directory manager,o=gluu')
        cert_folder = StringType(default="/etc/certs")
        conf_dir = StringType(default="/etc/gluu/conf")
        saml_type = StringType(default="shibboleth")

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="oxidp")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def image(self):
        return "oxidp"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


class NginxContainer(Container):
    class ContainerAttrs(BaseModel):
        cert_folder = StringType(default="/etc/certs")

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="nginx")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def image(self):
        return "nginx"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")


class OxasimbaContainer(Container):
    class ContainerAttrs(BaseModel):
        ldap_binddn = StringType(default='cn=directory manager,o=gluu')
        cert_folder = StringType(default="/etc/certs")
        conf_dir = StringType(default="/etc/gluu/conf")

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="oxasimba")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def image(self):
        return "oxasimba"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def truststore_fn(self):
        return "/usr/lib/jvm/default-java/jre/lib/security/cacerts"


class OxelevenContainer(Container):
    class ContainerAttrs(BaseModel):
        pass

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="oxeleven")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def image(self):
        return "oxeleven"
