# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import json
import os.path
import time

from .base import BaseSetup
from .oxauth_setup import OxauthSetup
from .oxtrust_setup import OxtrustSetup


class LdapSetup(BaseSetup):
    @property
    def ldif_base(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/base.ldif')

    @property
    def ldif_appliance(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/appliance.ldif')

    @property
    def ldif_attributes(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/attributes.ldif')

    @property
    def ldif_scopes(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/scopes.ldif')

    @property
    def ldif_clients(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/clients.ldif')

    @property
    def ldif_people(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/people.ldif')

    @property
    def ldif_groups(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/groups.ldif')

    @property
    def ldif_site(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/o_site.ldif')

    @property
    def ldif_scripts(self):  # pragma: no cover
        return self.get_template_path('salt/opendj/ldif/scripts.ldif')

    @property
    def ldif_files(self):  # pragma: no cover
        # List of initial ldif files
        return [
            self.ldif_base,
            self.ldif_appliance,
            self.ldif_attributes,
            self.ldif_scopes,
            self.ldif_clients,
            self.ldif_people,
            self.ldif_groups,
            self.ldif_site,
            self.ldif_scripts,
        ]

    @property
    def index_json(self):  # pragma: no cover
        return self.get_template_path("salt/opendj/opendj_index.json")

    @property
    def ldap_setup_properties(self):  # pragma: no cover
        return self.get_template_path("salt/opendj/opendj-setup.properties")

    @property
    def schema_files(self):  # pragma: no cover
        templates = [
            "salt/opendj/schema/77-customAttributes.ldif",
            "salt/opendj/schema/101-ox.ldif",
            "salt/opendj/schema/96-eduperson.ldif",
            "salt/opendj/schema/100-user.ldif",
        ]
        return map(self.get_template_path, templates)

    def write_ldap_pw(self):
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
        self.logger.info("deleting temporary LDAP password")
        self.salt.cmd(
            self.node.id,
            'cmd.run',
            ['rm -f {}'.format(self.node.ldap_pass_fn)],
        )

    def add_ldap_schema(self):
        ctx = {
            "inumOrgFN": self.cluster.inum_org_fn,
        }

        # render schema templates
        for schema_file in self.schema_files:
            src = schema_file
            basename = os.path.basename(src)
            dest = os.path.join(self.node.schema_folder, basename)
            self.render_template(src, dest, ctx)

    def setup_opendj(self):
        src = self.ldap_setup_properties
        dest = os.path.join(self.node.ldap_base_folder, os.path.basename(src))
        ctx = {
            "ldap_hostname": self.node.id,
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

        self.logger.info("running dsjavaproperties")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            [self.node.ldap_ds_java_prop_command],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def configure_opendj(self):
        config_changes = [
            ['set-global-configuration-prop', '--set', 'single-structural-objectclass-behavior:accept'],
            ['set-attribute-syntax-prop', '--syntax-name', '"Directory String"', '--set', 'allow-zero-length-values:true'],
            ['set-password-policy-prop', '--policy-name', '"Default Password Policy"', '--set', 'allow-pre-encoded-passwords:true'],
            ['set-log-publisher-prop', '--publisher-name', '"File-Based Audit Logger"', '--set', 'enabled:true'],
            ['create-backend', '--backend-name', 'site', '--set', 'base-dn:o=site', '--type local-db', '--set', 'enabled:true'],
        ]

        for changes in config_changes:
            dsconfigCmd = " ".join([
                self.node.ldap_dsconfig_command, '--trustAll', '--no-prompt',
                '--hostname', self.node.weave_ip,
                '--port', self.node.ldap_admin_port,
                '--bindDN', '"%s"' % self.node.ldap_binddn,
                '--bindPasswordFile', self.node.ldap_pass_fn,
            ] + changes)
            self.logger.info("configuring opendj config changes: {}".format(dsconfigCmd))
            jid = self.salt.cmd_async(self.node.id, 'cmd.run', [dsconfigCmd])
            self.salt.subscribe_event(jid, self.node.id)

    def index_opendj(self, backend):
        with open(self.index_json, 'r') as fp:
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
                        '--hostName', self.node.weave_ip,
                        '--port', self.node.ldap_admin_port,
                        '--bindDN', '"%s"' % self.node.ldap_binddn,
                        '-j', self.node.ldap_pass_fn,
                        '--trustAll', '--noPropertiesFile', '--no-prompt',
                    ])
                    jid = self.salt.cmd_async(self.node.id, 'cmd.run', [index_cmd])
                    self.salt.subscribe_event(jid, self.node.id)

    def import_ldif(self):
        # template's context
        ctx = {
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauthClient_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "encoded_ldap_pw": self.cluster.encoded_ldap_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "inumAppliance": self.cluster.inum_appliance,
            "hostname": self.node.weave_ip,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "ldaps_port": self.node.ldaps_port,
            "ldap_binddn": self.node.ldap_binddn,
            "inumOrg": self.cluster.inum_org,
            "inumOrgFN": self.cluster.inum_org_fn,
            "orgName": self.cluster.org_name,
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
                '--hostname', self.node.weave_ip,
                '--port', self.node.ldap_admin_port,
                '--bindDN', '"%s"' % self.node.ldap_binddn,
                '-j', self.node.ldap_pass_fn,
                '--append', '--trustAll',
            ])
            self.logger.info("importing {}".format(file_basename))
            jid = self.salt.cmd_async(self.node.id, 'cmd.run', [importCmd])
            self.salt.subscribe_event(jid, self.node.id)

    def export_opendj_public_cert(self):
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
        setup_obj = LdapSetup(existing_node, self.cluster, logger=self.logger)

        # creates temporary password file
        setup_obj.write_ldap_pw()

        base_dns = ("o=gluu", "o=site",)
        for base_dn in base_dns:
            enable_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "enable",
                "--host1", existing_node.weave_ip,
                "--port1", existing_node.ldap_admin_port,
                "--bindDN1", "'{}'".format(existing_node.ldap_binddn),
                "--bindPasswordFile1", self.node.ldap_pass_fn,
                "--replicationPort1", existing_node.ldap_replication_port,
                "--host2", self.node.weave_ip,
                "--port2", self.node.ldap_admin_port,
                "--bindDN2", "'{}'".format(self.node.ldap_binddn),
                "--bindPasswordFile2", self.node.ldap_pass_fn,
                "--replicationPort2", self.node.ldap_replication_port,
                "--adminUID", "admin",
                "--adminPasswordFile", self.node.ldap_pass_fn,
                "--baseDN", "'{}'".format(base_dn),
                "--secureReplication1", "--secureReplication2",
                "-X", "-n",
            ])
            self.logger.info("enabling {!r} replication between {} and {}".format(
                base_dn, existing_node.weave_ip, self.node.weave_ip,
            ))
            jid = self.salt.cmd_async(self.node.id, "cmd.run", [enable_cmd])
            self.salt.subscribe_event(jid, self.node.id)

            # wait before initializing the replication to ensure it
            # has been enabled
            time.sleep(10)

            init_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "initialize",
                "--baseDN", "'{}'".format(base_dn),
                "--adminUID", "admin",
                "--adminPasswordFile", self.node.ldap_pass_fn,
                "--hostSource", existing_node.weave_ip,
                "--portSource", existing_node.ldap_admin_port,
                "--hostDestination", self.node.weave_ip,
                "--portDestination", self.node.ldap_admin_port,
                "-X", "-n"
            ])
            self.logger.info("initializing {!r} replication between {} and {}".format(
                base_dn, existing_node.weave_ip, self.node.weave_ip,
            ))
            jid = self.salt.cmd_async(self.node.id, "cmd.run", [init_cmd])
            self.salt.subscribe_event(jid, self.node.id)
            time.sleep(5)

        # cleanups temporary password file
        setup_obj.delete_ldap_pw()

    def add_auto_startup_entry(self):
        # add supervisord entry
        run_cmd = ' '.join([self.node.ldap_run_command, '--quiet'])
        payload = """
[program:{}]
command={}
""".format(self.node.type, run_cmd)

        self.logger.info("adding supervisord entry")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["echo '{}' >> /etc/supervisor/conf.d/supervisord.conf".format(payload)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def start_opendj(self):
        run_cmd = ' '.join([self.node.ldap_run_command, '--quiet'])
        self.logger.info("running opendj server")
        jid = self.salt.cmd_async(
            self.node.id,
            'cmd.run',
            ["{}".format(run_cmd)],
        )
        self.salt.subscribe_event(jid, self.node.id)

    def setup(self):
        self.write_ldap_pw()
        self.add_ldap_schema()
        self.setup_opendj()
        # add auto startup entry
        self.add_auto_startup_entry()
        self.start_opendj()
        self.configure_opendj()
        self.index_opendj("site")
        self.index_opendj("userRoot")

        try:
            peer_node = self.cluster.get_ldap_objects()[-1]
            # Initialize data from existing ldap node.
            # To create fully meshed replication, update the other
            # ldap node to use this new ldap node as a master.
            self.replicate_from(peer_node)
        except IndexError:
            self.import_ldif()

        self.export_opendj_public_cert()
        self.delete_ldap_pw()
        return True

    def render_ox_ldap_props(self):
        for oxauth in self.cluster.get_oxauth_objects():
            setup_obj = OxauthSetup(oxauth, self.cluster, logger=self.logger,
                                    template_dir=self.template_dir)
            setup_obj.render_ldap_props_template()

        for oxtrust in self.cluster.get_oxtrust_objects():
            setup_obj = OxtrustSetup(oxtrust, self.cluster, logger=self.logger,
                                     template_dir=self.template_dir)
            setup_obj.render_ldap_props_template()

    def after_setup(self):
        """Runs post-setup.
        """
        self.render_ox_ldap_props()

        # modify oxIDPAuthentication entry when we have more LDAP nodes
        self.modify_oxidp_auth()

        # add ldap entry into ``/etc/hosts`` file
        for oxauth in self.cluster.get_oxauth_objects():
            setup_obj = OxauthSetup(oxauth, self.cluster, logger=self.logger,
                                    template_dir=self.template_dir)
            setup_obj.add_ldap_host_entry(self.node)

        for oxtrust in self.cluster.get_oxtrust_objects():
            setup_obj = OxtrustSetup(oxtrust, self.cluster, logger=self.logger,
                                     template_dir=self.template_dir)
            setup_obj.add_ldap_host_entry(self.node)

    def teardown(self):
        self.modify_oxidp_auth()

        # remove ldap entry from ``/etc/hosts`` file
        for oxauth in self.cluster.get_oxauth_objects():
            setup_obj = OxauthSetup(oxauth, self.cluster, logger=self.logger,
                                    template_dir=self.template_dir)
            setup_obj.remove_ldap_host_entry(self.node)

        for oxtrust in self.cluster.get_oxtrust_objects():
            setup_obj = OxtrustSetup(oxtrust, self.cluster, logger=self.logger,
                                     template_dir=self.template_dir)
            setup_obj.remove_ldap_host_entry(self.node)

        # stop the replication agreement
        ldap_num = len(self.cluster.get_ldap_objects())
        if ldap_num > 0:
            self.write_ldap_pw()
            self.logger.info("disabling replication")
            disable_repl_cmd = " ".join([
                "{}/bin/dsreplication".format(self.node.ldap_base_folder),
                "disable",
                "--hostname", self.node.weave_ip,
                "--port", self.node.ldap_admin_port,
                "--adminUID", "admin",
                "--adminPasswordFile", self.node.ldap_pass_fn,
                "-X", "-n", "--disableAll",
            ])
            self.salt.cmd(self.node.id, "cmd.run", [disable_repl_cmd])
            self.delete_ldap_pw()

        # stop the server
        stop_cmd = "{}/bin/stop-ds".format(self.node.ldap_base_folder)
        self.salt.cmd(self.node.id, "cmd.run", [stop_cmd])
        self.render_ox_ldap_props()
        self.after_teardown()

    @property
    def ldif_appliance_mod(self):
        return "salt/opendj/ldif/appliance-mod.ldif"

    def modify_oxidp_auth(self):
        nodes = self.cluster.get_ldap_objects()
        self.render_jinja_template(
            self.ldif_appliance_mod,
            "/opt/opendj/ldif/appliance-mod.ldif",
            ctx={
                "nodes": nodes,
                "inumAppliance": self.cluster.inum_appliance,
                "ldap_binddn": self.node.ldap_binddn,
                "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            },
        )
        self.write_ldap_pw()
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
        self.delete_ldap_pw()
