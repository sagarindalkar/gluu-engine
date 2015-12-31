# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
from glob import iglob
import json
import os.path
import time

import ldap as ldaplib

from .base import BaseSetup
from .oxauth_setup import OxauthSetup
from .oxtrust_setup import OxtrustSetup
from .oxidp_setup import OxidpSetup
from ..utils import generate_base64_contents
from ..model import STATE_SUCCESS


class LdapSetup(BaseSetup):
    @property
    def ldif_files(self):  # pragma: no cover
        """List of initial ldif files.
        """
        templates = [
            'nodes/opendj/ldif/base.ldif',
            'nodes/opendj/ldif/appliance.ldif',
            'nodes/opendj/ldif/attributes.ldif',
            'nodes/opendj/ldif/scopes.ldif',
            'nodes/opendj/ldif/clients.ldif',
            'nodes/opendj/ldif/people.ldif',
            'nodes/opendj/ldif/groups.ldif',
            'nodes/opendj/ldif/o_site.ldif',
            'nodes/opendj/ldif/scripts.ldif',
        ]
        return map(self.get_template_path, templates)

    @property
    def schema_files(self):  # pragma: no cover
        """List of predefined LDAP schema files.
        """
        templates = [
            "nodes/opendj/schema/77-customAttributes.ldif",
            "nodes/opendj/schema/101-ox.ldif",
            "nodes/opendj/schema/96-eduperson.ldif",
            "nodes/opendj/schema/100-user.ldif",
        ]
        return map(self.get_template_path, templates)

    def write_ldap_pw(self):
        """Writes temporary LDAP password into a file.

        It is recommended to remove the file after finishing
        any operation that requires password. Calling ``delete_ldap_pw``
        method will remove this password file.
        """
        self.logger.info("writing temporary LDAP password")

        local_dest = os.path.join(self.build_dir, ".pw")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write(self.cluster.decrypted_admin_pw)

        self.salt.cmd(
            self.node.id, "cmd.run",
            ["mkdir -p {}".format(os.path.dirname(self.node.ldap_pass_fn))],
        )
        self.salt.copy_file(self.node.id, local_dest, self.node.ldap_pass_fn)

    def delete_ldap_pw(self):
        """Removes temporary LDAP password.
        """
        self.logger.info("deleting temporary LDAP password")
        self.salt.cmd(
            self.node.id,
            'cmd.run',
            ['rm -f {}'.format(self.node.ldap_pass_fn)],
        )

    def add_ldap_schema(self):
        """Renders and copies predefined LDAP schema files into minion.
        """
        ctx = {
            "inum_org_fn": self.cluster.inum_org_fn,
        }
        for schema_file in self.schema_files:
            src = schema_file
            basename = os.path.basename(src)
            dest = os.path.join(self.node.schema_folder, basename)
            self.render_template(src, dest, ctx)

    def setup_opendj(self):
        """Setups OpenDJ server without actually running the server
        in post-installation step.
        """
        src = self.get_template_path("nodes/opendj/opendj-setup.properties")
        dest = os.path.join(self.node.ldap_base_folder, os.path.basename(src))
        ctx = {
            "ldap_hostname": self.node.domain_name,
            "ldap_port": self.node.ldap_port,
            "ldaps_port": self.node.ldaps_port,
            "ldap_jmx_port": self.node.ldap_jmx_port,
            "ldap_admin_port": self.node.ldap_admin_port,
            "ldap_binddn": self.node.ldap_binddn,
            "ldapPassFn": self.node.ldap_pass_fn,
        }
        self.render_template(src, dest, ctx)

        setupCmd = " ".join([
            self.node.ldap_setup_command,
            '--no-prompt', '--cli', '--doNotStart', '--acceptLicense',
            '--propertiesFilePath', dest,
        ])

        self.logger.info("running opendj setup")
        jid = self.salt.cmd_async(self.node.id, 'cmd.run',
                                  ["{}".format(setupCmd)])
        self.salt.subscribe_event(jid, self.node.id)

        # Use predefined dsjavaproperties
        self.logger.info("running dsjavaproperties")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            [self.node.ldap_ds_java_prop_command],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def configure_opendj(self):
        """Configures OpenDJ.
        """
        config_changes = [
            ['set-global-configuration-prop', '--set', 'single-structural-objectclass-behavior:accept'],
            ['set-attribute-syntax-prop', '--syntax-name', '"Directory String"', '--set', 'allow-zero-length-values:true'],
            ['set-password-policy-prop', '--policy-name', '"Default Password Policy"', '--set', 'allow-pre-encoded-passwords:true'],
            ['set-log-publisher-prop', '--publisher-name', '"File-Based Audit Logger"', '--set', 'enabled:true'],
            ['create-backend', '--backend-name', 'site', '--set', 'base-dn:o=site', '--type local-db', '--set', 'enabled:true'],
            ['set-global-configuration-prop', '--set', 'reject-unauthenticated-requests:true'],
        ]

        for changes in config_changes:
            dsconfigCmd = " ".join([
                self.node.ldap_dsconfig_command, '--trustAll', '--no-prompt',
                '--hostname', self.node.domain_name,
                '--port', self.node.ldap_admin_port,
                '--bindDN', '"%s"' % self.node.ldap_binddn,
                '--bindPasswordFile', self.node.ldap_pass_fn,
            ] + changes)
            self.logger.info("configuring opendj config changes: {}".format(dsconfigCmd))
            jid = self.salt.cmd_async(self.node.id, 'cmd.run', [dsconfigCmd])
            self.salt.subscribe_event(jid, self.node.id)
            time.sleep(1)

    def index_opendj(self, backend):
        """Creates required index in OpenDJ server.
        """
        json_tmpl = self.get_template_path("nodes/opendj/opendj_index.json")
        with open(json_tmpl, 'r') as fp:
            index_json = json.load(fp)

        for attr_map in index_json:
            attr_name = attr_map['attribute']

            for index_type in attr_map["index"]:
                for backend_name in attr_map["backend"]:
                    if backend_name != backend:
                        continue

                    self.logger.info(
                        "creating {} attribute for {} index "
                        "in {} backend".format(attr_name, index_type, backend)
                    )

                    index_cmd = " ".join([
                        self.node.ldap_dsconfig_command,
                        'create-local-db-index',
                        '--backend-name', backend,
                        '--type', 'generic',
                        '--index-name', attr_name,
                        '--set', 'index-type:%s' % index_type,
                        '--set', 'index-entry-limit:4000',
                        '--hostName', self.node.domain_name,
                        '--port', self.node.ldap_admin_port,
                        '--bindDN', '"%s"' % self.node.ldap_binddn,
                        '-j', self.node.ldap_pass_fn,
                        '--trustAll', '--noPropertiesFile', '--no-prompt',
                    ])
                    jid = self.salt.cmd_async(self.node.id, 'cmd.run', [index_cmd])
                    self.salt.subscribe_event(jid, self.node.id)
                    time.sleep(1)

    def import_ldif(self):
        """Renders and imports predefined ldif files.
        """
        # template's context
        ctx = {
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "encoded_ldap_pw": self.cluster.encoded_ldap_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "inum_appliance": self.cluster.inum_appliance,
            "hostname": self.node.domain_name,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "ldaps_port": self.node.ldaps_port,
            "ldap_binddn": self.node.ldap_binddn,
            "inum_org": self.cluster.inum_org,
            "inum_org_fn": self.cluster.inum_org_fn,
            "org_name": self.cluster.org_name,
            "scim_rp_client_id": self.cluster.scim_rp_client_id,
            "oxtrust_hostname": "localhost:8443",
        }

        ldifFolder = '%s/ldif' % self.node.ldap_base_folder
        self.salt.cmd(
            self.node.id,
            "cmd.run",
            ["mkdir -p {}".format(ldifFolder)]
        )

        # render templates
        for ldif_file in self.ldif_files:
            src = ldif_file
            file_basename = os.path.basename(src)
            dest = os.path.join(ldifFolder, file_basename)
            self.render_template(src, dest, ctx)

            if file_basename == "o_site.ldif":
                backend_id = "site"
            else:
                backend_id = "userRoot"

            importCmd = " ".join([
                self.node.import_ldif_command,
                '--ldifFile', dest,
                '--backendID', backend_id,
                '--hostname', self.node.domain_name,
                '--port', self.node.ldap_admin_port,
                '--bindDN', '"%s"' % self.node.ldap_binddn,
                '-j', self.node.ldap_pass_fn,
                '--append', '--trustAll',
                # "--rejectFile", "/tmp/rejected-{}".format(file_basename),
            ])
            self.logger.info("importing {}".format(file_basename))
            jid = self.salt.cmd_async(self.node.id, 'cmd.run', [importCmd])
            self.salt.subscribe_event(jid, self.node.id)

    def export_opendj_public_cert(self):
        """Exports OpenDJ public certificate.
        """
        # Load password to acces OpenDJ truststore
        openDjPinFn = '%s/config/keystore.pin' % self.node.ldap_base_folder
        openDjTruststoreFn = '%s/config/truststore' % self.node.ldap_base_folder
        openDjPin = "`cat {}`".format(openDjPinFn)

        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run"],
            [
                ["mkdir -p {}".format(os.path.dirname(self.node.opendj_cert_fn))],
                ["touch {}".format(self.node.opendj_cert_fn)],
            ],
        )

        # Export public OpenDJ certificate
        self.logger.info("exporting OpenDJ certificate")
        cmdsrt = ' '.join([
            self.node.keytool_command, '-exportcert',
            '-keystore', openDjTruststoreFn,
            '-storepass', openDjPin,
            '-file', self.node.opendj_cert_fn,
            '-alias', 'server-cert',
            '-rfc',
        ])
        jid = self.salt.cmd_async(self.node.id, 'cmd.run', [cmdsrt])
        self.salt.subscribe_event(jid, self.node.id)

        # Import OpenDJ certificate into java truststore
        cmdstr = ' '.join([
            "/usr/bin/keytool", "-import", "-trustcacerts", "-alias",
            "{}_opendj".format(self.node.weave_ip),
            "-file", self.node.opendj_cert_fn,
            "-keystore", self.node.truststore_fn,
            "-storepass", "changeit", "-noprompt",
        ])
        self.logger.info("importing OpenDJ certificate into Java truststore")
        jid = self.salt.cmd_async(self.node.id, 'cmd.run', [cmdstr])
        self.salt.subscribe_event(jid, self.node.id)

    def replicate_from(self, existing_node):
        """Setups a replication between two OpenDJ servers.

        The data will be replicated from existing OpenDJ server.

        :param existing_node: OpenDJ server where the initial data
                              will be replicated from.
        """
        setup_obj = LdapSetup(existing_node, self.cluster,
                              self.app, logger=self.logger)

        # creates temporary password file
        setup_obj.write_ldap_pw()

        base_dns = ("o=gluu", "o=site",)
        for base_dn in base_dns:
            enable_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "enable",
                "--host1", existing_node.domain_name,
                "--port1", existing_node.ldap_admin_port,
                "--bindDN1", "'{}'".format(existing_node.ldap_binddn),
                "--bindPasswordFile1", self.node.ldap_pass_fn,
                "--replicationPort1", existing_node.ldap_replication_port,
                "--host2", self.node.domain_name,
                "--port2", self.node.ldap_admin_port,
                "--bindDN2", "'{}'".format(self.node.ldap_binddn),
                "--bindPasswordFile2", self.node.ldap_pass_fn,
                "--replicationPort2", self.node.ldap_replication_port,
                "--adminUID", "admin",
                "--adminPasswordFile", self.node.ldap_pass_fn,
                "--baseDN", "'{}'".format(base_dn),
                "--secureReplication1", "--secureReplication2",
                "-X", "-n", "-Q",
            ])
            self.logger.info("enabling {!r} replication between {} and {}".format(
                base_dn, existing_node.weave_ip, self.node.weave_ip,
            ))
            resp = self.salt.cmd(self.node.id, "cmd.run", [enable_cmd])
            self.logger.info(resp.get(self.node.id, "").strip())

            # wait before initializing the replication to ensure it
            # has been enabled
            time.sleep(10)

            init_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "initialize",
                "--baseDN", "'{}'".format(base_dn),
                "--adminUID", "admin",
                "--adminPasswordFile", self.node.ldap_pass_fn,
                "--hostSource", existing_node.domain_name,
                "--portSource", existing_node.ldap_admin_port,
                "--hostDestination", self.node.domain_name,
                "--portDestination", self.node.ldap_admin_port,
                "-X", "-n", "-Q",
            ])
            self.logger.info("initializing {!r} replication between {} and {}".format(
                base_dn, existing_node.weave_ip, self.node.weave_ip,
            ))
            resp = self.salt.cmd(self.node.id, "cmd.run", [init_cmd])
            self.logger.info(resp.get(self.node.id, "").strip())
            time.sleep(5)

        # cleanups temporary password file
        setup_obj.delete_ldap_pw()

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        # add supervisord entry
        payload = """
[program:opendj]
command=/opt/opendj/bin/start-ds --quiet -N
"""

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def setup(self):
        """Runs the actual setup.
        """
        self.write_ldap_pw()
        self.add_ldap_schema()
        self.import_custom_schema()
        self.setup_opendj()
        self.reconfigure_minion()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        self.configure_opendj()
        self.index_opendj("site")
        self.index_opendj("userRoot")

        try:
            peer_node = self.cluster.get_ldap_objects()[0]
            # Initialize data from existing ldap node.
            # To create fully meshed replication, update the other
            # ldap node to use this new ldap node as a master.
            self.replicate_from(peer_node)
        except IndexError:
            self.import_ldif()
            self.import_base64_scim_config()

        self.export_opendj_public_cert()
        self.delete_ldap_pw()
        return True

    def notify_ox(self):
        """Notify all ox* apps.

        Typically this method should be called after adding/removing
        any OpenDJ server.
        """
        # notify oxAuth to re-render ``oxauth-ldap.propertia
        for oxauth in self.cluster.get_oxauth_objects():
            setup_obj = OxauthSetup(oxauth, self.cluster,
                                    self.app, logger=self.logger)
            setup_obj.render_ldap_props_template()

        # notify oxTrust to re-render ``oxtrust-ldap.properties``
        for oxtrust in self.cluster.get_oxtrust_objects():
            setup_obj = OxtrustSetup(oxtrust, self.cluster,
                                     self.app, logger=self.logger)
            setup_obj.render_ldap_props_template()
            # a hack to force oxTrust re-generate SAML metadata
            setup_obj.restart_tomcat()

        # notify oxIdp to re-render ``oxidp-ldap.properties``
        # and import OpenDJ certficate
        for oxidp in self.cluster.get_oxidp_objects():
            setup_obj = OxidpSetup(oxidp, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.render_ldap_props_template()
            setup_obj.import_ldap_certs()

    def after_setup(self):
        """Runs post-setup.
        """
        if self.node.state == STATE_SUCCESS:
            self.notify_ox()

        # modify oxIDPAuthentication entry when we have more LDAP nodes
        self.write_ldap_pw()
        time.sleep(5)
        self.modify_oxidp_auth()

        # if this is the first ldap, import configuration.ldif
        if len(self.cluster.get_ldap_objects()) == 1:
            self.import_base64_config()
        else:
            peer_node = self.cluster.get_ldap_objects()[0]
            self.modify_oxtrust_config(peer_node)

        # remove password file
        self.delete_ldap_pw()

    def teardown(self):
        """Teardowns the node.
        """
        self.write_ldap_pw()
        time.sleep(5)
        self.modify_oxidp_auth()

        # stop the replication agreement
        ldap_num = len(self.cluster.get_ldap_objects())
        if ldap_num > 0:
            self.disable_replication()
            # wait for process to run in the background
            time.sleep(5)

        # stop the server
        stop_cmd = "supervisorctl stop ldap"
        self.salt.cmd(self.node.id, "cmd.run", [stop_cmd])

        # remove password file
        self.delete_ldap_pw()

        # modify oxtrust config
        if self.node.state == STATE_SUCCESS:
            try:
                peer_node = self.cluster.get_ldap_objects()[0]
                self.modify_oxtrust_config(peer_node)
            except IndexError:
                pass
            self.notify_ox()
        self.after_teardown()

    def modify_oxidp_auth(self):
        """Updates oxIDPAuthentication entry in LDAP.
        """
        nodes = self.cluster.get_ldap_objects()
        self.copy_rendered_jinja_template(
            "nodes/opendj/ldif/appliance-mod.ldif",
            "/opt/opendj/ldif/appliance-mod.ldif",
            ctx={
                "nodes": nodes,
                "inum_appliance": self.cluster.inum_appliance,
                "ldap_binddn": self.node.ldap_binddn,
                "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            },
        )
        ldapmod_cmd = " ".join([
            "/opt/opendj/bin/ldapmodify",
            "-f /opt/opendj/ldif/appliance-mod.ldif",
            "-j {}".format(self.node.ldap_pass_fn),
            "-p {}".format(self.node.ldaps_port),
            "-D '{}'".format(self.node.ldap_binddn),
            "-Z -X",
        ])
        self.logger.info("modifying oxIDPAuthentication entry")
        self.salt.cmd(self.node.id, "cmd.run", [ldapmod_cmd])

    def import_custom_schema(self):
        """Copies user-defined LDAP schema into the node.
        """
        files = iglob("{}/*.ldif".format(self.app.config["CUSTOM_LDAP_SCHEMA_DIR"]))
        for file_ in files:
            if not os.path.isfile(file_):
                continue
            basename = os.path.basename(file_)
            dest = "{}/{}".format(self.node.schema_folder, basename)
            self.logger.info("copying {}".format(basename))
            self.salt.copy_file(self.node.id, file_, dest)

    def disable_replication(self):
        """Disable replication setup for current node.
        """
        self.logger.info("disabling replication for {}".format(self.node.weave_ip))
        disable_repl_cmd = " ".join([
            "{}/bin/dsreplication".format(self.node.ldap_base_folder),
            "disable",
            "--hostname", self.node.domain_name,
            "--port", self.node.ldap_admin_port,
            "--adminUID", "admin",
            "--adminPasswordFile", self.node.ldap_pass_fn,
            "-X", "-n", "--disableAll",
        ])
        self.salt.cmd(self.node.id, "cmd.run", [disable_repl_cmd])

    def import_base64_config(self):
        """Copies rendered configuration.ldif and imports into LDAP.
        """
        ctx = {
            "inum_appliance": self.cluster.inum_appliance,
            "oxauth_config_base64": generate_base64_contents(self.render_oxauth_config(), 1),
            "oxauth_static_conf_base64": generate_base64_contents(self.render_oxauth_static_config(), 1),
            "oxauth_error_base64": generate_base64_contents(self.render_oxauth_error_config(), 1),
            "oxauth_openid_key_base64": generate_base64_contents(self.gen_openid_key(), 1),
            "oxtrust_config_base64": generate_base64_contents(self.render_oxtrust_config(), 1),
            "oxtrust_cache_refresh_base64": generate_base64_contents(self.render_oxtrust_cache_refresh(), 1),
            "oxtrust_import_person_base64": generate_base64_contents(self.render_oxtrust_import_person(), 1),
            "oxidp_config_base64": generate_base64_contents(self.render_oxidp_config(), 1),
        }
        self.copy_rendered_jinja_template(
            "nodes/opendj/ldif/configuration.ldif",
            "/opt/opendj/ldif/configuration.ldif",
            ctx,
        )
        import_cmd = " ".join([
            self.node.import_ldif_command,
            '--ldifFile', "/opt/opendj/ldif/configuration.ldif",
            '--backendID', "userRoot",
            '--hostname', self.node.domain_name,
            '--port', self.node.ldap_admin_port,
            '--bindDN', '"%s"' % self.node.ldap_binddn,
            '-j', self.node.ldap_pass_fn,
            '--append', '--trustAll',
            # "--rejectFile", "/tmp/rejected-configuration.ldif",
        ])
        self.logger.info("importing configuration.ldif")
        jid = self.salt.cmd_async(self.node.id, 'cmd.run', [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def gen_openid_key(self):
        """Generates OpenID Connect key.
        """
        def extra_jar_abspath(jar):
            return "/opt/gluu/lib/{}".format(jar)

        jars = map(extra_jar_abspath, [
            "bcprov-jdk16-1.46.jar",
            "jettison-1.3.jar",
            "commons-lang-2.6.jar",
            "log4j-1.2.17.jar",
            "commons-codec-1.5.jar",
            "oxauth-model-2.4.1.Final.jar",
            "oxauth-server-2.4.1.Final.jar",
        ])
        classpath = ":".join(jars)
        resp = self.salt.cmd(
            self.node.id,
            "cmd.run",
            ["java -cp {} org.xdi.oxauth.util.KeyGenerator".format(classpath)],
        )
        return resp.get(self.node.id, "")

    def render_oxauth_config(self):
        """Renders oxAuth configuration.
        """
        src = "nodes/oxauth/oxauth-config.json"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "inum_appliance": self.cluster.inum_appliance,
            "inum_org": self.cluster.inum_org,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxauth_static_config(self):
        """Renders oxAuth static configuration.
        """
        src = "nodes/oxauth/oxauth-static-conf.json"
        ctx = {
            "inum_org": self.cluster.inum_org,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxauth_error_config(self):
        """Renders oxAuth error configuration.
        """
        src = "nodes/oxauth/oxauth-errors.json"
        return self.render_jinja_template(src)

    def render_oxtrust_config(self):
        """Renders oxTrust configuration.
        """
        src = "nodes/oxtrust/oxtrust-config.json"
        ldap_hosts = ",".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "inum_appliance": self.cluster.inum_appliance,
            "inum_org": self.cluster.inum_org,
            "admin_email": self.cluster.admin_email,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "shib_jks_fn": self.cluster.shib_jks_fn,
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "inum_org_fn": self.cluster.inum_org_fn,
            "encoded_shib_jks_pw": self.cluster.encoded_shib_jks_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "truststore_fn": self.node.truststore_fn,
            "ldap_hosts": ldap_hosts,
            "config_generation": "true",
            "scim_rs_client_id": self.cluster.scim_rs_client_id,
            "oxtrust_hostname": "localhost:8443",
        }
        return self.render_jinja_template(src, ctx)

    def render_oxtrust_cache_refresh(self):
        """Renders oxTrust CR configuration.
        """
        src = "nodes/oxtrust/oxtrust-cache-refresh.json"
        ldap_hosts = self.cluster.get_ldap_objects()
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxidp_config(self):
        """Renders oxIdp configuration.
        """
        src = "nodes/oxidp/oxidp-config.json"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "oxtrust_hostname": "localhost:8443",
        }
        return self.render_jinja_template(src, ctx)

    def modify_oxtrust_config(self, node):
        """Updates oxTrust configuration in LDAP.
        """
        self.logger.info("modifying oxTrust configuration")

        # we're using weave IP instead since domain_name is available
        # only from inside the container
        uri = "ldaps://{}:{}".format(node.weave_ip, node.ldaps_port)

        # credentials to authenticate to LDAP server
        user = node.ldap_binddn
        passwd = self.cluster.decrypted_admin_pw

        # base DN for oxtrust config
        oxtrust_base = ",".join([
            "ou=oxtrust",
            "ou=configuration",
            "inum={}".format(self.cluster.inum_appliance),
            "ou=appliances",
            "o=gluu",
        ])
        scope = ldaplib.SCOPE_BASE

        conn = self.get_ldap_conn(uri, user, passwd)
        if conn:
            dn, attrs = self.search_from_ldap(conn, oxtrust_base, scope)
            if dn:
                ox_rev = str(int(attrs["oxRevision"][0]) + 1)

                # we only care about ``idpLdapServer``
                app_conf = json.loads(attrs["oxTrustConfApplication"][0])
                app_conf["idpLdapServer"] = ",".join([
                    "{}:{}".format(node_.domain_name, node_.ldaps_port)
                    for node_ in self.cluster.get_ldap_objects()
                ])
                serialized_app_conf = json.dumps(app_conf)

                # we only care about ``inumConfig`` -> ``servers``
                cr_conf = json.loads(attrs["oxTrustConfCacheRefresh"][0])
                cr_conf["inumConfig"]["servers"] = [
                    "{}:{}".format(node_.domain_name, node_.ldaps_port)
                    for node_ in self.cluster.get_ldap_objects()
                ]
                serialized_cr_conf = json.dumps(cr_conf)

                # list of attributes need to be updated
                modlist = [
                    (ldaplib.MOD_REPLACE, "oxRevision", ox_rev),
                    (ldaplib.MOD_REPLACE, "oxTrustConfApplication",
                     serialized_app_conf),
                    (ldaplib.MOD_REPLACE, "oxTrustConfCacheRefresh",
                     serialized_cr_conf),
                ]
                # update the attributes
                conn.modify_s(dn, modlist)

            # release the connection to LDAP server
            conn.unbind_s()

    def get_ldap_conn(self, uri, user, passwd):
        """Establishes LDAP connection.
        """
        ldaplib.set_option(ldaplib.OPT_X_TLS_REQUIRE_CERT,
                           ldaplib.OPT_X_TLS_NEVER)

        try:
            conn = ldaplib.initialize(uri)
            conn.set_option(ldaplib.OPT_REFERRALS, 0)
            conn.set_option(ldaplib.OPT_PROTOCOL_VERSION, 3)
            conn.set_option(ldaplib.OPT_X_TLS, ldaplib.OPT_X_TLS_DEMAND)
            conn.set_option(ldaplib.OPT_X_TLS_DEMAND, True)
            conn.set_option(ldaplib.OPT_DEBUG_LEVEL, 255)
            conn.simple_bind_s(user, passwd)
        except ldaplib.SERVER_DOWN as exc:
            self.logger.error(exc.message)
        return conn

    def search_from_ldap(self, conn, base, scope,
                         filterstr="(objectClass=*)",
                         attrlist=None, attrsonly=0):
        """Searches for entries in LDAP.
        """
        try:
            result = conn.search_s(base, scope)
            ret = result[0]
        except ldaplib.NO_SUCH_OBJECT as exc:
            self.logger.error(exc.message)
            ret = ("", {})
        return ret

    def import_base64_scim_config(self):
        """Copies SCIM configuration (scim.ldif) into the node
        and imports into LDAP.
        """
        ctx = {
            "inum_org": self.cluster.inum_org,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "scim_rs_client_id": self.cluster.scim_rs_client_id,
            "scim_rp_client_id": self.cluster.scim_rp_client_id,
            "scim_rs_client_base64_jwks": generate_base64_contents(self.gen_openid_key(), 1),
            "scim_rp_client_base64_jwks": generate_base64_contents(self.gen_openid_key(), 1),
            "oxtrust_hostname": "localhost:8443",
        }
        self.copy_rendered_jinja_template(
            "nodes/opendj/ldif/scim.ldif",
            "/opt/opendj/ldif/scim.ldif",
            ctx,
        )
        import_cmd = " ".join([
            self.node.import_ldif_command,
            '--ldifFile', "/opt/opendj/ldif/scim.ldif",
            '--backendID', "userRoot",
            '--hostname', self.node.domain_name,
            '--port', self.node.ldap_admin_port,
            '--bindDN', '"%s"' % self.node.ldap_binddn,
            '-j', self.node.ldap_pass_fn,
            '--append', '--trustAll',
            # "--rejectFile", "/tmp/rejected-scim.ldif",
        ])
        self.logger.info("importing scim.ldif")
        jid = self.salt.cmd_async(self.node.id, 'cmd.run', [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def render_oxtrust_import_person(self):
        """Renders oxTrust import person configuration.
        """
        src = "nodes/oxtrust/oxtrust-import-person.json"
        ctx = {}
        return self.render_jinja_template(src, ctx)
