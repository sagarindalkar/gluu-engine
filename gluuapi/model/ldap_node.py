# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from flask_restful.fields import String
from flask_restful_swagger import swagger

from .base import BaseModel


@swagger.model
class LdapNode(BaseModel):
    # Swager Doc
    resource_fields = {
        'id': String(attribute='Node unique identifier'),
        'type': String(attribute='Node type'),
        'cluster_id': String(attribute='Cluster ID'),
        'provider_id': String(attribute='Provider ID'),
        'ip': String(attribute='IP address of the node'),
        'ldap_binddn': String(attribute='LDAP super user Bind DN. Probably should leave it default cn=directory manager.'),
        'ldap_port': String(attribute='Non SSL LDAP port (not used)'),
        'ldaps_port': String(attribute='LDAPS port'),
        'ldap_admin_port': String(attribute='Admin port'),
        'ldap_jmx_port': String(attribute='JMX port (not used)'),
        "name": String,
        "weave_ip": String,
        "state": String,
        "domain_name": String,
    }

    def __init__(self):
        self.id = ''
        self.cluster_id = ""
        self.provider_id = ""
        self.name = ''
        self.ldap_type = "opendj"
        self.ip = ""
        self.weave_ip = ""
        self.weave_prefixlen = ""
        self.type = 'ldap'
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
        return 1
