# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from schematics.types import IntType
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


class LdapContainer(Container):
    class ContainerAttrs(BaseModel):
        ldap_type = StringType(default="opendj")
        truststore_fn = StringType(
            default='/usr/lib/jvm/java-7-openjdk-amd64'
                    '/jre/lib/security/cacerts',
        )
        cert_folder = StringType(default="/etc/certs")
        opendj_cert_fn = StringType(default='/etc/certs/opendj.crt')
        ldap_binddn = StringType(default='cn=directory manager')
        ldap_port = StringType(default='1389')
        ldaps_port = StringType(default='1636')
        ldap_jmx_port = StringType(default='1689')
        ldap_admin_port = StringType(default='4444')
        ldap_replication_port = StringType(default="8989")
        ldap_base_folder = StringType(default='/opt/opendj')
        ldap_start_timeout = IntType(default=30)
        ldap_setup_command = StringType(default='/opt/opendj/setup')
        ldap_run_command = StringType(default='/opt/opendj/bin/start-ds')
        ldap_dsconfig_command = StringType(default="/opt/opendj/bin/dsconfig")
        ldap_ds_java_prop_command = StringType(
            default="/opt/opendj/bin/dsjavaproperties",
        )
        ldap_pass_fn = StringType(default='/home/ldap/.pw')
        schema_folder = StringType(
            default="/opt/opendj/template/config/schema",
        )
        org_custom_schema = StringType(
            default="/opt/opendj/config/schema/100-user.ldif",
        )

    id = StringType(default=lambda: str(uuid.uuid4()))
    cluster_id = StringType()
    node_id = StringType()
    name = StringType()
    type = StringType(default="ldap")
    state = StringType()
    hostname = StringType()
    cid = StringType()
    container_attrs = PolyModelType(ContainerAttrs, strict=False)
    _pyobject = StringType()

    @property
    def ldap_pass_fn(self):
        return self._resolve_container_attr("ldap_pass_fn")

    @property
    def schema_folder(self):
        return self._resolve_container_attr("schema_folder")

    @property
    def ldap_base_folder(self):
        return self._resolve_container_attr("ldap_base_folder")

    @property
    def ldap_port(self):
        return self._resolve_container_attr("ldap_port")

    @property
    def ldap_jmx_port(self):
        return self._resolve_container_attr("ldap_jmx_port")

    @property
    def ldap_admin_port(self):
        return self._resolve_container_attr("ldap_admin_port")

    @property
    def ldap_setup_command(self):
        return self._resolve_container_attr("ldap_setup_command")

    @property
    def ldap_ds_java_prop_command(self):
        return self._resolve_container_attr("ldap_ds_java_prop_command")

    @property
    def ldap_dsconfig_command(self):
        return self._resolve_container_attr("ldap_dsconfig_command")

    @property
    def opendj_cert_fn(self):
        return self._resolve_container_attr("opendj_cert_fn")

    @property
    def truststore_fn(self):
        return self._resolve_container_attr("truststore_fn")

    @property
    def ldap_replication_port(self):
        return self._resolve_container_attr("ldap_replication_port")

    @property
    def keytool_command(self):
        # Full path to java keytool command
        return '/usr/bin/keytool'

    @property
    def openssl_command(self):
        # Full path to openssl command
        return '/usr/bin/openssl'

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 1

    @property
    def image(self):
        # currently only supports opendj
        return "gluuopendj"


class OxauthContainer(Container):
    class ContainerAttrs(BaseModel):
        truststore_fn = StringType(
            default='/usr/lib/jvm/java-7-openjdk-amd64'
                    '/jre/lib/security/cacerts',
        )
        ldap_binddn = StringType(default='cn=directory manager')
        cert_folder = StringType(default="/etc/certs")
        oxauth_lib = StringType(default="/opt/tomcat/webapps/oxauth/WEB-INF/lib")
        tomcat_home = StringType(default="/opt/tomcat")
        tomcat_conf_dir = StringType(default="/opt/tomcat/conf")
        tomcat_log_folder = StringType(default="/opt/tomcat/logs")

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
    def tomcat_conf_dir(self):
        return self._resolve_container_attr("tomcat_conf_dir")

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 2

    @property
    def image(self):
        return "gluuoxauth"


class OxtrustContainer(Container):
    class ContainerAttrs(BaseModel):
        truststore_fn = StringType(
            default='/usr/lib/jvm/java-7-openjdk-amd64'
                    '/jre/lib/security/cacerts',
        )
        ldap_binddn = StringType(default='cn=directory manager')
        cert_folder = StringType(default="/etc/certs")
        tomcat_home = StringType(default="/opt/tomcat")
        tomcat_conf_dir = StringType(default="/opt/tomcat/conf")
        tomcat_log_folder = StringType(default="/opt/tomcat/logs")

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
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 3

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def tomcat_conf_dir(self):
        return self._resolve_container_attr("tomcat_conf_dir")

    @property
    def image(self):
        return "gluuoxtrust"

    @property
    def truststore_fn(self):
        return self._resolve_container_attr("truststore_fn")


class OxidpContainer(Container):
    class ContainerAttrs(BaseModel):
        truststore_fn = StringType(
            default='/usr/lib/jvm/java-7-openjdk-amd64'
                    '/jre/lib/security/cacerts',
        )
        ldap_binddn = StringType(default='cn=directory manager')
        cert_folder = StringType(default="/etc/certs")
        tomcat_home = StringType(default="/opt/tomcat")
        tomcat_conf_dir = StringType(default="/opt/tomcat/conf")
        tomcat_log_folder = StringType(default="/opt/tomcat/logs")
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
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 4

    @property
    def image(self):
        return "gluuoxidp"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def truststore_fn(self):
        return self._resolve_container_attr("truststore_fn")


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
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 5

    @property
    def image(self):
        return "gluunginx"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")


class OxasimbaContainer(Container):
    class ContainerAttrs(BaseModel):
        truststore_fn = StringType(
            default='/usr/lib/jvm/java-7-openjdk-amd64'
                    '/jre/lib/security/cacerts',
        )
        ldap_binddn = StringType(default='cn=directory manager')
        cert_folder = StringType(default="/etc/certs")
        tomcat_home = StringType(default="/opt/tomcat")
        tomcat_conf_dir = StringType(default="/opt/tomcat/conf")
        tomcat_log_folder = StringType(default="/opt/tomcat/logs")

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
    def recovery_priority(self):
        return 6

    @property
    def image(self):
        return "gluuoxasimba"

    @property
    def cert_folder(self):
        return self._resolve_container_attr("cert_folder")

    @property
    def tomcat_conf_dir(self):
        return self._resolve_container_attr("tomcat_conf_dir")
