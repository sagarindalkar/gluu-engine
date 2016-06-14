# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import functools
import os

import click
from crochet import setup as crochet_setup
from daemonocle import Daemon

from .app import create_app
from .database import db
from .log import configure_global_logging
from .machine import Machine
# from .task import LicenseWatcherTask
from .setup.signals import connect_setup_signals
from .setup.signals import connect_teardown_signals

# global context settings
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def run_app(app, use_reloader=True):
    crochet_setup()

    # if not app.debug:
    #     LicenseWatcherTask(app).perform_job()

    connect_setup_signals()
    connect_teardown_signals()

    app.run(
        host=app.config["HOST"],
        port=int(app.config["PORT"]),
        use_reloader=use_reloader,
    )


class GluuDaemonCLI(click.MultiCommand):
    def __init__(self, **kwargs):
        # make daemon as partial so we can pass params
        # when calling commands
        self.daemon = functools.partial(Daemon)
        super(GluuDaemonCLI, self).__init__(
            context_settings={"obj": {}},
            **kwargs
        )

    def list_commands(self, ctx):
        return self.daemon().list_actions()

    def get_command(self, ctx, name):
        @click.pass_context
        def subcommand(ctx):
            # use worker and pidfile from context
            daemon = self.daemon(worker=ctx.obj["worker"],
                                 pidfile=ctx.obj["pidfile"])
            daemon.do_action(name)

        # attach doc from original callable so it will appear
        # in CLI output
        subcommand.__doc__ = self.daemon().get_action(name).__doc__

        cmd = click.command(name)(subcommand)
        return cmd

@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


@main.command(cls=GluuDaemonCLI)
@click.option(
    "--pidfile",
    default="/var/run/gluuengine.pid",
    metavar="<pidfile>",
    type=click.Path(resolve_path=True, file_okay=True, dir_okay=True,
                    writable=True, readable=True),
    help="Path to PID file (default to /var/run/gluuengine.pid).",
)
@click.option(
    "--logfile",
    default="/var/log/gluuengine/api.log",
    metavar="<logfile>",
    type=click.Path(resolve_path=True, file_okay=True, dir_okay=True,
                    writable=True, readable=True),
    help="Path to log file (default to /var/log/gluuengine/api.log).",
)
@click.pass_context
def daemon(ctx, pidfile, logfile):
    """Manage the daemon.
    """
    configure_global_logging(logfile)
    app = create_app()
    ctx.obj["pidfile"] = pidfile
    ctx.obj["worker"] = functools.partial(run_app, app, use_reloader=False)


@main.command()
@click.option(
    "--auto-reload",
    is_flag=True,
    help="Enable/disable auto-reload feature",
)
def runserver(auto_reload):
    """Run development server with/without auto-reloader.
    """
    configure_global_logging()
    app = create_app()
    run_app(app, use_reloader=auto_reload)

@main.command()
def runserver2():
    """Run development server with auto-reloader.
    """
    configure_global_logging()
    app = create_app()
    run_app(app=app, use_reloader=False)


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

    click.echo("distributing custom {} files".format(ox["name"]))

    app = create_app()
    mc = Machine()

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
                {"node_id": node.id, "type": type_},
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
