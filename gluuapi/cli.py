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
from .log import configure_global_logging
from .task import LicenseExpirationTask
from .task import OxidpWatcherTask
# from .task import OxauthWatcherTask
# from .task import OxtrustWatcherTask
from .database import db

# global context settings
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def check_salt():
    if not os.environ.get("SALT_MASTER_IPADDR"):
        raise SystemExit("Unable to get salt-master IP address. "
                         "Make sure the SALT_MASTER_IPADDR "
                         "environment variable is set.")


def run_app(app, use_reloader=True):
    crochet_setup()

    if not app.debug:
        LicenseExpirationTask(app).perform_job()

    OxidpWatcherTask(app).perform_job()
    # OxauthWatcherTask(app).perform_job()
    # OxtrustWatcherTask(app).perform_job()

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
    default="/var/run/gluuapi.pid",
    metavar="<pidfile>",
    type=click.Path(resolve_path=True, file_okay=True, dir_okay=True,
                    writable=True, readable=True),
    help="Path to PID file (default to /var/run/gluuapi.pid).",
)
@click.option(
    "--logfile",
    default="/var/log/gluuapi.log",
    metavar="<logfile>",
    type=click.Path(resolve_path=True, file_okay=True, dir_okay=True,
                    writable=True, readable=True),
    help="Path to log file (default to /var/log/gluuapi.log).",
)
@click.pass_context
def daemon(ctx, pidfile, logfile):
    """Manage the daemon.
    """
    check_salt()
    configure_global_logging(logfile)
    app = create_app()
    ctx.obj["pidfile"] = pidfile
    ctx.obj["worker"] = functools.partial(run_app, app, use_reloader=False)


@main.command()
def runserver():
    """Run development server with auto-reloader.
    """
    check_salt()
    configure_global_logging()
    app = create_app()
    run_app(app)


@main.command("upgrade-providers")
def upgrade_providers():
    """Upgrade providers to use cluster ID.
    """
    click.echo("checking providers having empty cluster_id")

    app = create_app()
    db.app = app

    providers = db.search_from_table(
        "providers",
        (db.where("cluster_id") == "") | (~db.where("cluster_id")),
    )
    for provider in providers:
        cluster_id = click.prompt(
            "cluster ID for {} provider {}".format(provider.type, provider.id)
        )
        cluster_exists = db.count_from_table(
            "clusters", db.where("id") == cluster_id,
        )
        if not cluster_exists:
            click.echo("cluster ID {} is not found".format(cluster_id))
        else:
            click.echo("attaching cluster {} to {} provider {}".format(
                cluster_id, provider.type, provider.id
            ))
            provider.cluster_id = cluster_id
            db.update(provider.id, provider, "providers")
            click.echo("cluster {} has been attached to {} provider {}".format(
                cluster_id, provider.type, provider.id
            ))
