# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os

import click

from .app import create_app
from .database import db
from .machine import Machine
from .registry import get_registry_cert
from .registry import REGISTRY_BASE_URL

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
        nodes = db.search_from_table(
            "nodes",
            {"$or": [{"type": "master"}, {"type": "worker"}]},
        )

    src = app.config[ox["override_dir_config"]]
    dest = src.replace(app.config[ox["override_dir_config"]],
                       ox["override_remote_dir"])

    for node in nodes:
        click.echo("copying {} to {}:{} recursively".format(
            src, node.name, dest
        ))
        mc.scp(src, "{}:{}".format(node.name, os.path.dirname(dest)),
               recursive=True)

        with app.app_context():
            containers = db.search_from_table(
                "containers",
                {"node_id": node.id, "type": type_, "state": "SUCCESS"},
            )

        for container in containers:
            # we only need to restart tomcat process inside the container
            click.echo(
                "restarting tomcat process inside {} container {} "
                "in {} node".format(ox["name"], container.cid, node.name)
            )
            mc.ssh(
                node.name,
                "sudo docker exec {} supervisorctl restart tomcat".format(container.cid),
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


@main.command("update-registry-cert")
def update_reg_cert():
    """Update and distribute registry certificate.
    """
    app = create_app()
    mc = Machine()

    with app.app_context():
        nodes = db.search_from_table(
            "nodes",
            {"$or": [{"type": "master"}, {"type": "worker"}]},
        )

        reg_cert = get_registry_cert(
            os.path.join(app.config["REGISTRY_CERT_DIR"], "ca.crt"),
            redownload=True,
        )

        for node in nodes:
            click.echo("copying registry cert to {} node".format(node.name))
            mc.ssh(
                node.name,
                "mkdir -p /etc/docker/certs.d/{}".format(REGISTRY_BASE_URL)
            )
            mc.scp(
                reg_cert,
                r"{}:/etc/docker/certs.d/{}/ca.crt".format(
                    node.name,
                    REGISTRY_BASE_URL,
                ),
            )
