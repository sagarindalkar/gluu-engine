# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import uuid

import click
from flask_migrate.cli import db as migrator

from .app import create_app
from .dockerclient import Docker
from .errors import DockerExecError
from .machine import Machine
from .model import Node
from .model import Container


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

    with app.app_context():
        nodes = Node.query.filter(Node.type.in_(["master", "worker"])).all()

        src = app.config[ox["override_dir_config"]]
        dest = src.replace(app.config[ox["override_dir_config"]],
                           ox["override_remote_dir"])

        for node in nodes:
            click.echo("copying {} to {}:{} recursively".format(
                src, node.name, dest
            ))

            mc.ssh(node.name, "mkdir -p {}".format(dest))
            mc.scp(src, "{}:{}".format(node.name, os.path.dirname(dest)),
                   recursive=True)

            containers = Container.query.filter_by(
                node_id=node.id, type=type_, state="SUCCESS",
            ).all()

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

    with app.app_context():
        master_node = Node.query.filter_by(type="master").first()

        if not master_node:
            click.echo("master node is not available; process cancelled")
            return

        mc = Machine()
        dk = Docker(mc.config(master_node.name),
                    mc.swarm_config(master_node.name))

        ngx_containers = Container.query.filter_by(
            type="nginx", state="SUCCESS",
        ).all()

        for ngx in ngx_containers:
            click.echo("copying {} to {}:/etc/certs/nginx.crt".format(ssl_cert, ngx.name))
            dk.copy_to_container(ngx.cid, ssl_cert, "/etc/certs/nginx.crt")
            click.echo("copying {} to {}:/etc/certs/nginx.key".format(ssl_key, ngx.name))
            dk.copy_to_container(ngx.cid, ssl_key, "/etc/certs/nginx.key")
            dk.exec_cmd(ngx.cid, "supervisorctl restart nginx")

        oxtrust = Container.query.filter_by(
            type="oxtrust", state="SUCCESS",
        ).first()

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
                click.echo("importing ssl cert into {} "
                           "keystore".format(oxtrust.name))
                dk.exec_cmd(oxtrust.cid, import_cmd)
            except DockerExecError as exc:
                if exc.exit_code == 1:
                    # certificate already imported
                    click.echo("certificate already imported")

    # mark the process as finished
    click.echo("distributing SSL cert and key is done")


# add db migrator commands
main.add_command(migrator)
