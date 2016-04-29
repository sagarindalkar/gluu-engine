# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import functools

import click
from crochet import setup as crochet_setup
from daemonocle import Daemon

from .app import create_app
from .log import configure_global_logging
from .task import LicenseExpirationTask
# from .task import OxidpWatcherTask
# from .task import OxauthWatcherTask
# from .task import OxtrustWatcherTask
# from .database import db
# from .helper import SaltHelper
# from .utils import run
from .setup.signals import connect_setup_signals
from .setup.signals import connect_teardown_signals

# global context settings
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def run_app(app, use_reloader=True):
    crochet_setup()

    if not app.debug:
        LicenseExpirationTask(app).perform_job()

    # FIXME: new oxtrust container setup doesn't put generated
    #        SAML config in same host where this app lives
    # OxidpWatcherTask(app).perform_job()

    # OxauthWatcherTask(app).perform_job()
    # OxtrustWatcherTask(app).perform_job()

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
    configure_global_logging(logfile)
    app = create_app()
    ctx.obj["pidfile"] = pidfile
    ctx.obj["worker"] = functools.partial(run_app, app, use_reloader=False)


@main.command()
def runserver():
    """Run development server with auto-reloader.
    """
    configure_global_logging()
    app = create_app()
    run_app(app)


# @main.command('distribute-payload')
# def distpayload():
#     volume_root = '/var/gluu/webapps/oxauth'
#     run('docker restart nginx_sfs')
#     master_ip = os.environ.get("SALT_MASTER_IPADDR")
#     providers = db.all('providers')
#     salt = SaltHelper()
#     cmd = 'wget -r -q -nH -np -R index.html* http://{}:9001 -P {}'.format(master_ip, volume_root)
#     for provider in providers:
#         salt.cmd(provider.hostname, 'cmd.run', cmd)
#     oxauths = db.search_from_table('nodes', ((db.where('type') == 'oxauth') & (db.where('state') == 'SUCCESS')))
#     cmd = "supervisorctl restart tomcat"
#     for oxauth in oxauths:
#         salt.cmd(oxauth.id, 'cmd.run', cmd)
