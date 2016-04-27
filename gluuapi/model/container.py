# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import uuid

from .base import BaseModel


class LdapContainer(BaseModel):
    resource_fields = dict.fromkeys([
        'id',
        'type',
        'cluster_id',
        'node_id',
        'ip',
        'ldap_binddn',
        'ldap_port',
        'ldaps_port',
        'ldap_admin_port',
        'ldap_jmx_port',
        "name",
        "weave_ip",
        "state",
        "domain_name",
    ])

    def __init__(self):
        # Node unique identifier
        self.id = ''
        self.cluster_id = ""
        self.node_id = ""
        self.name = ''
        self.ldap_type = "opendj"
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = 'ldap'
        self.image = "gluuopendj"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        # Filesystem path to Java truststore
        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'

        # Filesystem path of the public certificate for OpenDJ
        self.opendj_cert_fn = '/etc/certs/opendj.crt'

        self.ldap_binddn = 'cn=directory manager'
        self.ldap_port = '1389'
        self.ldaps_port = '1636'
        self.ldap_jmx_port = '1689'
        self.ldap_admin_port = '4444'
        self.ldap_replication_port = "8989"

        # Where to install OpenDJ, usually /opt/opendj
        self.ldap_base_folder = '/opt/opendj'

        # How long to wait for LDAP to start
        self.ldap_start_timeout = 30

        # Full path to opendj setup command
        self.ldap_setup_command = '%s/setup' % self.ldap_base_folder

        # Full path to opendj run command
        self.ldap_run_command = '%s/bin/start-ds' % self.ldap_base_folder

        # Full path to dsconfig command
        self.ldap_dsconfig_command = "%s/bin/dsconfig" % self.ldap_base_folder

        # # Full path to create-rc command
        # self.ldapDsCreateRcCommand = "%s/bin/create-rc-script" % self.ldap_base_folder

        # Full path to dsjavaproperties command
        self.ldap_ds_java_prop_command = "%s/bin/dsjavaproperties" % self.ldap_base_folder

        # Full path to import command
        self.import_ldif_command = '%s/bin/import-ldif' % self.ldap_base_folder

        # # Full path to encode password
        # self.ldapEncodePWCommand = '%s/bin/encode-password' % self.ldap_base_folder

        # Temporary path to store ldap password (should be removed)
        self.ldap_pass_fn = '/home/ldap/.pw'

        # Full path of template schema to copy to the opendj server
        self.schema_folder = "%s/template/config/schema" % self.ldap_base_folder
        self.org_custom_schema = "%s/config/schema/100-user.ldif" % self.ldap_base_folder
        # # Full path of the destination of the init script
        # self.ldap_start_script = '/etc/init.d/opendj'

        # Full path to java keytool command
        self.keytool_command = '/usr/bin/keytool'

        # Full path to openssl command
        self.openssl_command = '/usr/bin/openssl'

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 1


class OxauthContainer(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "name",
        "type",
        "ip",
        "cluster_id",
        "node_id",
        "weave_ip",
        "state",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.node_id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxauth"
        self.image = "gluuoxauth"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'
        self.ldap_binddn = 'cn=directory manager'

        self.cert_folder = "/etc/certs"
        self.oxauth_lib = "/opt/tomcat/webapps/oxauth/WEB-INF/lib"

        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 2


class OxtrustContainer(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "name",
        "type",
        "ip",
        "cluster_id",
        "node_id",
        "weave_ip",
        "state",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.node_id = ""
        self.name = ""
        self.hostname = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxtrust"
        self.image = "gluuoxtrust"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.ldap_binddn = 'cn=directory manager'
        self.cert_folder = "/etc/certs"
        self.truststore_fn = '/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts'

        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 6


class OxidpContainer(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "type",
        "cluster_id",
        "node_id",
        "ip",
        "name",
        "weave_ip",
        "state",
        "saml_type",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.node_id = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxidp"
        self.image = "gluuoxidp"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"
        self.truststore_fn = "/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts"
        self.ldap_binddn = "cn=directory manager"
        self.saml_type = "shibboleth"

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 4


class NginxContainer(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "cluster_id",
        "node_id",
        "ip",
        "cid",
        "weave_ip",
        "name",
        "type",
        "state",
        # "domain_name",
        "hostname",
    ])

    def __init__(self):
        # self.id = ""
        self.id = str(uuid.uuid4())
        self.cid = ""
        self.name = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.cluster_id = ""
        self.node_id = ""
        self.type = "nginx"
        self.image = "gluunginx"
        self.state = ""
        self.setup_logpath = ""
        # self.domain_name = ""
        self.cert_folder = "/etc/certs"
        self.hostname = ""

    @property
    def recovery_priority(self):
        """Gets recovery priority number used by recovery script.
        """
        return 3


class OxasimbaContainer(BaseModel):
    resource_fields = dict.fromkeys([
        "id",
        "type",
        "cluster_id",
        "node_id",
        "ip",
        "name",
        "weave_ip",
        "state",
        "saml_type",
        "domain_name",
    ])

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.node_id = ""
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = "oxasimba"
        self.image = "gluuoxasimba"
        self.state = ""
        self.setup_logpath = ""
        self.domain_name = ""

        self.cert_folder = "/etc/certs"
        self.tomcat_home = "/opt/tomcat"
        self.tomcat_conf_dir = "/opt/tomcat/conf"
        self.tomcat_log_folder = "/opt/tomcat/logs"
        self.truststore_fn = "/usr/lib/jvm/java-7-openjdk-amd64/jre/lib/security/cacerts"
        self.ldap_binddn = "cn=directory manager"

    @property
    def recovery_priority(self):
        return 5
