# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import uuid

import click

from .app import create_app
from .database import db
from .dockerclient import Docker
from .errors import DockerExecError
from .machine import Machine
from .model import CLUSTER_SCHEMA
from .model import CONTAINER_SCHEMA
from .model import CONTAINER_LOG_SCHEMA
from .model import NODE_SCHEMA
from .model import PROVIDER_SCHEMA
from .model import LICENSE_KEY_SCHEMA


# global context settings
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


def _distribute_ox_files(type_):
    assert type_ in ("oxauth", "oxtrust",), "unsupported ox app"

    ox_map = {
        "oxauth": {
            "name": "oxAuth",
            "override_dir_config": "OXAUTH_OVERRIDE_DIR",
            "override_remote_dir": "/var/gluu/webapps/oxauth",
        },
        "oxtrust": {
            "name": "oxTrust",
            "override_dir_config": "OXTRUST_OVERRIDE_DIR",
            "override_remote_dir": "/var/gluu/webapps/oxtrust",
        },
    }
    ox = ox_map[type_]
    app = create_app()
    mc = Machine()

    click.echo("distributing custom {} files".format(ox["name"]))

    mnodes = db.search_from_table("nodes", {"type": "master"})
    wnodes = db.search_from_table("nodes", {"type": "worker"})
    nodes = mnodes + wnodes

    src = app.config[ox["override_dir_config"]]
    dest = src.replace(app.config[ox["override_dir_config"]],
                       ox["override_remote_dir"])

    for node in nodes:
        click.echo("copying {} to {}:{} recursively".format(
            src, node.name, dest
        ))
        mc.scp(src, "{}:{}".format(node.name, os.path.dirname(dest)),
               recursive=True)

        containers = db.search_from_table(
            "containers",
            {"node_id": node.id, "type": type_, "state": "SUCCESS"},
        )

        for container in containers:
            # we only need to restart jetty process inside the container
            click.echo(
                "restarting jetty process inside {} container {} "
                "in {} node".format(ox["name"], container.cid, node.name)
            )
            mc.ssh(
                node.name,
                "sudo docker exec {} supervisorctl restart jetty".format(container.cid),
            )


@main.command("distribute-oxauth-files")
def distribute_oxauth_files():
    """Distribute custom oxAuth files.
    """
    _distribute_ox_files("oxauth")


@main.command("distribute-oxtrust-files")
def distribute_oxtrust_files():
    """Distribute custom oxTrust files.
    """
    _distribute_ox_files("oxtrust")


@main.command("distribute-ssl-cert")
def distribute_ssl_cert():
    """Distribute SSL certificate and key.
    """
    app = create_app()

    ssl_cert = os.path.join(app.config["SSL_CERT_DIR"], "nginx.crt")
    if not os.path.exists(ssl_cert):
        click.echo("{} is not available; process cancelled".format(ssl_cert))
        return

    ssl_key = os.path.join(app.config["SSL_CERT_DIR"], "nginx.key")
    if not os.path.exists(ssl_key):
        click.echo("{} is not available; process cancelled".format(ssl_key))
        return

    try:
        master_node = db.search_from_table("nodes", {"type": "master"})[0]
    except IndexError:
        master_node = None

    if not master_node:
        click.echo("master node is not available; process cancelled")
        return

    mc = Machine()
    dk = Docker(mc.config(master_node.name),
                mc.swarm_config(master_node.name))

    ngx_containers = db.search_from_table(
        "containers",
        {"type": "nginx", "state": "SUCCESS"},
    )
    for ngx in ngx_containers:
        click.echo("copying {} to {}:/etc/certs/nginx.crt".format(ssl_cert, ngx.name))
        dk.copy_to_container(ngx.cid, ssl_cert, "/etc/certs/nginx.crt")
        click.echo("copying {} to {}:/etc/certs/nginx.key".format(ssl_key, ngx.name))
        dk.copy_to_container(ngx.cid, ssl_key, "/etc/certs/nginx.key")
        dk.exec_cmd(ngx.cid, "supervisorctl restart nginx")

    # oxTrust relies on nginx cert and key, hence we need to update it
    try:
        oxtrust = db.search_from_table(
            "containers",
            {"type": "oxtrust", "state": "SUCCESS"},
        )[0]
    except IndexError:
        oxtrust = None

    if oxtrust:
        click.echo("copying {} to {}:/etc/certs/nginx.crt".format(ssl_cert, oxtrust.name))
        dk.copy_to_container(oxtrust.cid, ssl_cert, "/etc/certs/nginx.crt")
        click.echo("copying {} to {}:/etc/certs/nginx.key".format(ssl_key, oxtrust.name))
        dk.copy_to_container(oxtrust.cid, ssl_key, "/etc/certs/nginx.key")

        der_cmd = "openssl x509 -outform der -in /etc/certs/nginx.crt " \
                  "-out /etc/certs/nginx.der"
        dk.exec_cmd(oxtrust.cid, der_cmd)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(uuid.uuid4()),
            "-file /etc/certs/nginx.der",
            "-keystore {}".format(oxtrust.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        import_cmd = '''sh -c "{}"'''.format(import_cmd)

        try:
            click.echo("importing ssl cert into {} keystore".format(oxtrust.name))
            dk.exec_cmd(oxtrust.cid, import_cmd)
        except DockerExecError as exc:
            if exc.exit_code == 1:
                # certificate already imported
                click.echo("certificate already imported")

    # mark the process as finished
    click.echo("distributing SSL cert and key is done")


@main.command("init-schema")
def init_schema():
    """Initialize schema for RDBMS backend.
    """
    app = create_app()

    if not app.config["DATABASE_URI"].startswith("mysql"):
        click.echo("database backend doesn't require preloaded schema")
        return

    with app.test_request_context():
        schema_list = [CLUSTER_SCHEMA, CONTAINER_SCHEMA, CONTAINER_LOG_SCHEMA,
                       NODE_SCHEMA, PROVIDER_SCHEMA, LICENSE_KEY_SCHEMA]

        for schema in schema_list:
            table = db.backend._get_table(schema["name"])

            for column, type_ in schema["columns"].iteritems():
                if not table._has_column(column):
                    click.echo("creating column {} in {} table".format(
                        column, table.table,
                    ))
                    table.create_column(column, type_)
