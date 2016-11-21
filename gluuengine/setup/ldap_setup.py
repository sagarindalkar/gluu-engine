# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import codecs
import json
import os.path
import time
from glob import iglob
from random import randint

from .base import BaseSetup
from .oxidp_setup import OxidpSetup
from ..utils import generate_base64_contents
from ..utils import get_sys_random_chars
from ..model import STATE_SUCCESS


class LdapSetup(BaseSetup):
    supervisor_reload_delay = 30

    @property
    def ldif_files(self):  # pragma: no cover
        """List of initial ldif files.
        """
        templates = [
            'opendj/ldif/base.ldif',
            'opendj/ldif/appliance.ldif',
            'opendj/ldif/attributes.ldif',
            'opendj/ldif/scopes.ldif',
            'opendj/ldif/clients.ldif',
            'opendj/ldif/people.ldif',
            'opendj/ldif/groups.ldif',
            'opendj/ldif/scripts.ldif',
            'opendj/ldif/asimba.ldif',
        ]
        return map(self.get_template_path, templates)

    def write_ldap_pw(self):
        """Writes temporary LDAP password into a file.

        It is recommended to remove the file after finishing
        any operation that requires password. Calling ``delete_ldap_pw``
        method will remove this password file.
        """
        self.logger.debug("writing temporary LDAP password")

        local_dest = os.path.join(self.build_dir, ".pw")
        with codecs.open(local_dest, "w", encoding="utf-8") as fp:
            fp.write(self.cluster.decrypted_admin_pw)

        self.docker.exec_cmd(
            self.container.cid,
            "mkdir -p {}".format(os.path.dirname(self.container.ldap_pass_fn)),
        )
        self.docker.copy_to_container(self.container.cid, local_dest, self.container.ldap_pass_fn)

    def delete_ldap_pw(self):
        """Removes temporary LDAP password.
        """
        self.logger.debug("deleting temporary LDAP password")
        self.docker.exec_cmd(
            self.container.cid,
            'rm -f {}'.format(self.container.ldap_pass_fn)
        )

    def add_ldap_schema(self):
        """Renders and copies predefined LDAP schema files into minion.
        """
        ctx = {
            "inum_org_fn": self.cluster.inum_org_fn,
        }
        src = self.get_template_path("opendj/schema/100-user.ldif")
        dest = os.path.join(self.container.schema_folder, "100-user.ldif")
        self.render_template(src, dest, ctx)

    def setup_opendj(self):
        """Setups OpenDJ server without actually running the server
        in post-installation step.
        """
        self.logger.info("running opendj setup")

        src = self.get_template_path("opendj/opendj-setup.properties")
        dest = os.path.join(self.container.ldap_base_folder, os.path.basename(src))
        ctx = {
            "ldap_hostname": self.ldap_failover_hostname(),
            "ldap_port": self.container.ldap_port,
            "ldaps_port": self.cluster.ldaps_port,
            "ldap_jmx_port": self.container.ldap_jmx_port,
            "ldap_admin_port": self.container.ldap_admin_port,
            "ldap_binddn": self.cluster.ldap_binddn,
            "ldap_pass_fn": self.container.ldap_pass_fn,
            "ldap_backend_type": "je",  # OpenDJ 3.0
        }
        self.render_template(src, dest, ctx)

        setup_cmd = " ".join([
            self.container.ldap_setup_command,
            '--no-prompt', '--cli', '--doNotStart', '--acceptLicense',
            '--propertiesFilePath', dest,
        ])
        self.docker.exec_cmd(self.container.cid, setup_cmd)
        self.docker.exec_cmd(self.container.cid, self.container.ldap_ds_java_prop_command)

    def configure_opendj(self):
        """Configures OpenDJ.
        """
        self.logger.info("configuring opendj")

        config_changes = [
            "set-global-configuration-prop --set single-structural-objectclass-behavior:accept",
            "set-attribute-syntax-prop --syntax-name 'Directory String' --set allow-zero-length-values:true",
            "set-password-policy-prop --policy-name 'Default Password Policy' --set allow-pre-encoded-passwords:true",
            "set-log-publisher-prop --publisher-name 'File-Based Audit Logger' --set enabled:true",
            "create-backend --backend-name site --set base-dn:o=site --type je --set enabled:true",  # OpenDJ 3.0
            "set-connection-handler-prop --handler-name 'LDAP Connection Handler' --set enabled:false",
            'set-access-control-handler-prop --remove global-aci:\'(targetattr!=\\"userPassword||authPassword||debugsearchindex||changes||changeNumber||changeType||changeTime||targetDN||newRDN||newSuperior||deleteOldRDN\\")(version 3.0; acl \\"Anonymous read access\\"; allow (read,search,compare) userdn=\\"ldap:///anyone\\";)\'',  # OpenDJ 3.0
            "set-global-configuration-prop --set reject-unauthenticated-requests:true",
            "set-password-policy-prop --policy-name 'Default Password Policy' --set default-password-storage-scheme:'Salted SHA-512'",
        ]

        for changes in config_changes:
            dsconfig_cmd = " ".join([
                self.container.ldap_dsconfig_command,
                '--trustAll',
                '--no-prompt',
                '--hostname', self.container.hostname,
                '--port', self.container.ldap_admin_port,
                '--bindDN', "'{}'".format(self.cluster.ldap_binddn),
                '--bindPasswordFile', self.container.ldap_pass_fn,
                changes,
            ])

            dsconfig_cmd = '''sh -c "{}"'''.format(dsconfig_cmd)
            self.docker.exec_cmd(self.container.cid, dsconfig_cmd)

    def index_opendj(self, backend):
        """Creates required index in OpenDJ server.
        """
        self.logger.info("indexing attributes for {} backend".format(backend))

        resp = self.docker.exec_cmd(self.container.cid, "cat /opt/opendj/opendj_index.json")  # noqa
        try:
            index_json = json.loads(resp.retval)
        except ValueError:
            self.logger.warn("unable to read JSON string from opendj_index.json")
            index_json = []

        for attr_map in index_json:
            attr_name = attr_map['attribute']

            for index_type in attr_map["index"]:
                for backend_name in attr_map["backend"]:
                    if backend_name != backend:
                        continue

                    index_cmd = " ".join([
                        self.container.ldap_dsconfig_command,
                        "create-backend-index",
                        '--backend-name', backend,
                        '--type', 'generic',
                        '--index-name', attr_name,
                        '--set', 'index-type:%s' % index_type,
                        '--set', 'index-entry-limit:4000',
                        '--hostName', self.container.hostname,
                        '--port', self.container.ldap_admin_port,
                        '--bindDN', "'{}'".format(self.cluster.ldap_binddn),
                        '-j', self.container.ldap_pass_fn,
                        '--trustAll', '--noPropertiesFile', '--no-prompt',
                    ])
                    self.docker.exec_cmd(self.container.cid, index_cmd)

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
            "hostname": self.ldap_failover_hostname(),
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "ldaps_port": self.cluster.ldaps_port,
            "ldap_binddn": self.cluster.ldap_binddn,
            "inum_org": self.cluster.inum_org,
            "inum_org_fn": self.cluster.inum_org_fn,
            "org_name": self.cluster.org_name,
            "scim_rp_client_id": self.cluster.scim_rp_client_id,
        }

        ldifFolder = '%s/ldif' % self.container.ldap_base_folder
        self.docker.exec_cmd(self.container.cid, "mkdir -p {}".format(ldifFolder))

        # render templates
        for ldif_file in self.ldif_files:
            src = ldif_file
            file_basename = os.path.basename(src)
            dest = os.path.join(ldifFolder, file_basename)
            self.render_template(src, dest, ctx)
            backend_id = "userRoot"
            self._run_import_ldif(dest, backend_id)

        # import o_site.ldif
        backend_id = "site"
        dest = "/opt/opendj/ldif/o_site.ldif"
        self._run_import_ldif(dest, backend_id)

    def export_opendj_cert(self):
        """Exports OpenDJ public certificate.
        """
        # Load password to acces OpenDJ truststore
        openDjPinFn = '%s/config/keystore.pin' % self.container.ldap_base_folder
        openDjTruststoreFn = '%s/config/truststore' % self.container.ldap_base_folder
        openDjPin = "`cat {}`".format(openDjPinFn)

        self.docker.exec_cmd(
            self.container.cid,
            "touch {}".format(self.container.opendj_cert_fn),
        )

        # Export public OpenDJ certificate
        self.logger.debug("exporting OpenDJ certificate")
        cmd = ' '.join([
            self.container.keytool_command, '-exportcert',
            '-keystore', openDjTruststoreFn,
            '-storepass', openDjPin,
            '-file', self.container.opendj_cert_fn,
            '-alias', 'server-cert',
            '-rfc',
        ])
        cmd = '''sh -c "{}"'''.format(cmd)
        self.docker.exec_cmd(self.container.cid, cmd)

    def import_opendj_cert(self):
        # Import OpenDJ certificate into java truststore
        self.logger.debug("importing OpenDJ certificate into Java truststore")
        cmd = ' '.join([
            "/usr/bin/keytool", "-import", "-trustcacerts",
            "-alias", self.container.hostname,
            "-file", self.container.opendj_cert_fn,
            "-keystore", self.container.truststore_fn,
            "-storepass", "changeit", "-noprompt",
        ])
        cmd = '''sh -c "{}"'''.format(cmd)
        self.docker.exec_cmd(self.container.cid, cmd)

    def replicate_from(self, peer):
        """Setups a replication between two OpenDJ servers.

        The data will be replicated from existing OpenDJ server.

        :param peer: OpenDJ server where the initial data
                              will be replicated from.
        """
        setup_obj = LdapSetup(peer, self.cluster,
                              self.app, logger=self.logger)

        # creates temporary password file
        setup_obj.write_ldap_pw()

        base_dns = ("o=gluu", "o=site",)

        self.logger.info("initializing and enabling replication between {} and {}".format(
            peer.hostname, self.container.hostname,
        ))
        for base_dn in base_dns:
            enable_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "enable",
                "--host1", peer.hostname,
                "--port1", peer.ldap_admin_port,
                "--bindDN1", "'{}'".format(self.cluster.ldap_binddn),
                "--bindPasswordFile1", self.container.ldap_pass_fn,
                "--replicationPort1", peer.ldap_replication_port,
                "--host2", self.container.hostname,
                "--port2", self.container.ldap_admin_port,
                "--bindDN2", "'{}'".format(self.cluster.ldap_binddn),
                "--bindPasswordFile2", self.container.ldap_pass_fn,
                "--replicationPort2", self.container.ldap_replication_port,
                "--adminUID", "admin",
                "--adminPasswordFile", self.container.ldap_pass_fn,
                "--baseDN", "'{}'".format(base_dn),
                "--secureReplication1", "--secureReplication2",
                "-X", "-n", "-Q",
            ])
            self.docker.exec_cmd(self.container.cid, enable_cmd)

            # wait before initializing the replication to ensure it
            # has been enabled
            time.sleep(10)

            init_cmd = " ".join([
                "/opt/opendj/bin/dsreplication", "initialize",
                "--baseDN", "'{}'".format(base_dn),
                "--adminUID", "admin",
                "--adminPasswordFile", self.container.ldap_pass_fn,
                "--hostSource", peer.hostname,
                "--portSource", peer.ldap_admin_port,
                "--hostDestination", self.container.hostname,
                "--portDestination", self.container.ldap_admin_port,
                "-X", "-n", "-Q",
            ])
            self.docker.exec_cmd(self.container.cid, init_cmd)
            time.sleep(5)

        # cleanups temporary password file
        setup_obj.delete_ldap_pw()

    def add_auto_startup_entry(self):
        """Adds supervisor program for auto-startup.
        """
        self.logger.debug("adding opendj config for supervisord")
        src = "opendj/opendj.conf"
        dest = "/etc/supervisor/conf.d/opendj.conf"
        self.copy_rendered_jinja_template(src, dest)

    def setup(self):
        """Runs the actual setup.
        """
        self.write_ldap_pw()
        self.add_ldap_schema()
        self.import_custom_schema()
        self.setup_opendj()
        self.add_auto_startup_entry()
        self.reload_supervisor()
        self.configure_opendj()

        self.index_opendj("site")
        self.index_opendj("userRoot")

        try:
            peer = self.cluster.get_containers(type_="ldap")[0]
            # Initialize data from existing ldap container.
            # To create fully meshed replication, update the other
            # ldap container to use this new ldap container as a master.
            self.replicate_from(peer)
        except IndexError:
            self.logger.info("importing data from ldif files")
            self.import_ldif()
            self.import_base64_scim_config()
            self.import_base64_config()

        self.export_opendj_cert()
        self.import_opendj_cert()
        self.delete_ldap_pw()
        return True

    def notify_ox(self):
        """Notify all ox* apps.

        Typically this method should be called after adding/removing
        any OpenDJ server.
        """
        # import all OpenDJ certficates because oxIdp checks matched
        # certificate
        for oxidp in self.cluster.get_containers(type_="oxidp"):
            setup_obj = OxidpSetup(oxidp, self.cluster,
                                   self.app, logger=self.logger)
            setup_obj.import_ldap_certs()

    def after_setup(self):
        """Runs post-setup.
        """
        if self.container.state == STATE_SUCCESS:
            self.notify_ox()

    def teardown(self):
        """Teardowns the container.
        """
        self.write_ldap_pw()

        # stop the replication agreement
        ldap_num = len(self.cluster.get_containers(type_="ldap"))
        if ldap_num > 0:
            self.disable_replication()
            # wait for process to run in the background
            time.sleep(5)

        # remove password file
        self.delete_ldap_pw()

        if self.container.state == STATE_SUCCESS:
            self.notify_ox()

    def import_custom_schema(self):
        """Copies user-defined LDAP schema into the container.
        """
        files = iglob("{}/*.ldif".format(self.app.config["CUSTOM_LDAP_SCHEMA_DIR"]))
        for file_ in files:
            if not os.path.isfile(file_):
                continue
            basename = os.path.basename(file_)
            dest = "{}/{}".format(self.container.schema_folder, basename)
            self.logger.debug("copying {}".format(basename))
            self.docker.copy_to_container(self.container.cid, file_, dest)

    def disable_replication(self):
        """Disable replication setup for current container.
        """
        self.logger.info("disabling replication for {}".format(self.container.hostname))
        disable_repl_cmd = " ".join([
            "{}/bin/dsreplication".format(self.container.ldap_base_folder),
            "disable",
            "--hostname", self.container.hostname,
            "--port", self.container.ldap_admin_port,
            "--adminUID", "admin",
            "--adminPasswordFile", self.container.ldap_pass_fn,
            "-X", "-n", "--disableAll",
        ])
        self.docker.exec_cmd(self.container.cid, disable_repl_cmd)

    def import_base64_config(self):
        """Copies rendered configuration.ldif and imports into LDAP.
        """
        # TODO: need to save file to /etc/certs/oxauth-keys.json?
        oxauth_jwks = self.gen_openid_key(
            self.cluster.oxauth_openid_jks_fn,
            self.cluster.oxauth_openid_jks_pass,
        )

        # TODO: need to save all rendered config as files?
        ctx = {
            "inum_appliance": self.cluster.inum_appliance,
            "oxauth_config_base64": generate_base64_contents(self.render_oxauth_config(), 1),
            "oxauth_static_conf_base64": generate_base64_contents(self.render_oxauth_static_config(), 1),
            "oxauth_error_base64": generate_base64_contents(self.render_oxauth_error_config(), 1),
            "oxauth_openid_key_base64": generate_base64_contents(oxauth_jwks, 1),
            "oxtrust_config_base64": generate_base64_contents(self.render_oxtrust_config(), 1),
            "oxtrust_cache_refresh_base64": generate_base64_contents(self.render_oxtrust_cache_refresh(), 1),
            "oxtrust_import_person_base64": generate_base64_contents(self.render_oxtrust_import_person(), 1),
            "oxidp_config_base64": generate_base64_contents(self.render_oxidp_config(), 1),
            "oxcas_config_base64": generate_base64_contents(self.render_oxcas_config(), 1),
            "oxasimba_config_base64": generate_base64_contents(self.render_oxasimba_config(), 1),
        }
        self.copy_rendered_jinja_template(
            "opendj/ldif/configuration.ldif",
            "/opt/opendj/ldif/configuration.ldif",
            ctx,
        )
        self._run_import_ldif("/opt/opendj/ldif/configuration.ldif", "userRoot")

    def gen_openid_key(self, jks_path, jks_pwd):
        """Generates OpenID Connect key.
        """
        default_openid_jks_dn_name = "CN=oxAuth CA Certificates"
        default_key_algs = "RS256 RS384 RS512 ES256 ES384 ES512"
        default_key_expiration = 365

        # create JKS with dummy key
        cmd = " ".join([
            'keytool', '-genkey',
            '-alias', 'dummy',
            '-keystore', jks_path,
            '-storepass', jks_pwd,
            '-keypass', jks_pwd,
            '-dname', "'{}'".format(default_openid_jks_dn_name),
        ])
        cmd = '''sh -c "{}"'''.format(cmd)
        self.docker.exec_cmd(self.container.cid, cmd)

        # Delete dummy key from JKS
        cmd = " ".join([
            'keytool', '-delete',
            '-alias', 'dummy',
            '-keystore', jks_path,
            '-storepass', jks_pwd,
            '-keypass', jks_pwd,
            '-dname', "'{}'".format(default_openid_jks_dn_name),
        ])
        cmd = '''sh -c "{}"'''.format(cmd)
        self.docker.exec_cmd(self.container.cid, cmd)

        def extra_jar_abspath(jar):
            return "/opt/gluu/lib/{}".format(jar)

        jars = map(extra_jar_abspath, [
            "bcprov-jdk15on-1.54.jar",
            "bcpkix-jdk15on-1.54.jar",
            "jettison-1.3.jar",
            "log4j-1.2.14.jar",
            "commons-lang-2.6.jar",
            "commons-codec-1.5.jar",
            "commons-cli-1.2.jar",
            "oxauth-model.jar",
            "oxauth-server.jar",
        ])

        cmd = " ".join([
            "java", "-Dlog4j.defaultInitOverride=true",
            "-cp", ":".join(jars),
            "org.xdi.oxauth.util.KeyGenerator",
            "-keystore", jks_path,
            "-keypasswd", jks_pwd,
            "-algorithms", default_key_algs,
            "-dnname", "'{}'".format(default_openid_jks_dn_name),
            "-expiration", "{}".format(default_key_expiration),
        ])
        resp = self.docker.exec_cmd(self.container.cid, cmd)
        return resp.retval

    def render_oxauth_config(self):
        """Renders oxAuth configuration.
        """
        src = "oxauth/oxauth-config.json"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "inum_appliance": self.cluster.inum_appliance,
            "inum_org": self.cluster.inum_org,
            "pairwise_calculation_key": get_sys_random_chars(randint(20, 30)),
            "pairwise_calculation_salt": get_sys_random_chars(randint(20, 30)),
            "oxauth_openid_jks_fn": self.cluster.oxauth_openid_jks_fn,
            "oxauth_openid_jks_pass": self.cluster.oxauth_openid_jks_pass,
            "default_openid_jks_dn_name": "CN=oxAuth CA Certificates",
        }
        return self.render_jinja_template(src, ctx)

    def render_oxauth_static_config(self):
        """Renders oxAuth static configuration.
        """
        src = "oxauth/oxauth-static-conf.json"
        ctx = {
            "inum_org": self.cluster.inum_org,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxauth_error_config(self):
        """Renders oxAuth error configuration.
        """
        src = "oxauth/oxauth-errors.json"
        return self.render_jinja_template(src)

    def render_oxtrust_config(self):
        """Renders oxTrust configuration.
        """
        src = "oxtrust/oxtrust-config.json"
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
            "truststore_fn": self.container.truststore_fn,
            "ldap_hosts": "{}:{}".format(self.ldap_failover_hostname(), self.cluster.ldaps_port),
            "config_generation": "true",
            "scim_rs_client_id": self.cluster.scim_rs_client_id,
            "scim_rs_client_jks_fn": "/etc/certs/scim-rs.jks",
            "scim_rs_client_jks_pass_encoded": self.cluster.scim_rs_client_jks_pass_encoded,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxtrust_cache_refresh(self):
        """Renders oxTrust CR configuration.
        """
        src = "oxtrust/oxtrust-cache-refresh.json"
        ctx = {
            "ldap_binddn": self.cluster.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": "{}:{}".format(self.ldap_failover_hostname(), self.cluster.ldaps_port),
        }
        return self.render_jinja_template(src, ctx)

    def render_oxidp_config(self):
        """Renders oxIdp configuration.
        """
        src = "oxidp/oxidp-config.json"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
        }
        return self.render_jinja_template(src, ctx)

    def import_base64_scim_config(self):
        """Copies SCIM configuration (scim.ldif) into the container
        and imports into LDAP.
        """
        scim_rs_client_jwks = self.gen_openid_key(
            self.cluster.scim_rs_client_jks_fn,
            self.cluster.scim_rs_client_jks_pass,
        )
        scim_rp_client_jwks = self.gen_openid_key(
            self.cluster.scim_rp_client_jks_fn,
            self.cluster.scim_rp_client_jks_pass,
        )

        ctx = {
            "inum_org": self.cluster.inum_org,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "scim_rs_client_id": self.cluster.scim_rs_client_id,
            "scim_rp_client_id": self.cluster.scim_rp_client_id,
            "scim_rs_client_base64_jwks": generate_base64_contents(scim_rs_client_jwks, 1),
            "scim_rp_client_base64_jwks": generate_base64_contents(scim_rp_client_jwks, 1),
        }
        self.copy_rendered_jinja_template(
            "opendj/ldif/scim.ldif",
            "/opt/opendj/ldif/scim.ldif",
            ctx,
        )
        self._run_import_ldif("/opt/opendj/ldif/scim.ldif", "userRoot")

    def render_oxtrust_import_person(self):
        """Renders oxTrust import person configuration.
        """
        src = "oxtrust/oxtrust-import-person.json"
        ctx = {}
        return self.render_jinja_template(src, ctx)

    def render_oxcas_config(self):
        """Renders oxCAS configuration.
        """
        src = "oxcas/oxcas-config.json"
        ctx = {
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
        }
        return self.render_jinja_template(src, ctx)

    def render_oxasimba_config(self):
        """Renders oxAsimba configuration.
        """
        src = "oxasimba/oxasimba-config.json"
        ctx = {
            "inum_org": self.cluster.inum_org,
        }
        return self.render_jinja_template(src, ctx)

    def _run_import_ldif(self, ldif_fn, backend_id):
        file_basename = os.path.basename(ldif_fn)
        if backend_id == "site":
            import_cmd = " ".join([
                "/opt/opendj/bin/import-ldif",
                '--ldifFile', ldif_fn,
                '--backendID', backend_id,
                '--hostname', self.container.hostname,
                '--port', self.container.ldap_admin_port,
                '--bindDN', "'{}'".format(self.cluster.ldap_binddn),
                '-j', self.container.ldap_pass_fn,
                '--trustAll',
            ])
        else:
            import_cmd = " ".join([
                "/opt/opendj/bin/ldapmodify",
                '--filename', ldif_fn,
                '--hostname', self.container.hostname,
                '--port', self.container.ldap_admin_port,
                '--bindDN', "'{}'".format(self.cluster.ldap_binddn),
                '-j', self.container.ldap_pass_fn,
                "--defaultAdd",
                "--continueOnError",
                "--useSSL",
                '--trustAll',
            ])

        self.logger.debug("importing {}".format(file_basename))
        self.docker.exec_cmd(self.container.cid, import_cmd)
