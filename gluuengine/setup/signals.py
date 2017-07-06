# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import time

from blinker import signal

from .oxtrust_setup import OxtrustSetup
from .oxidp_setup import OxidpSetup
from .nginx_setup import NginxSetup
# from .oxeleven_setup import OxelevenSetup


def notify_oxtrust(ngx):
    with ngx.app.app_context():
        try:
            oxtrust = ngx.node.get_containers(type_="oxtrust")[0]
            setup_obj = OxtrustSetup(oxtrust, ngx.cluster, ngx.app, ngx.logger)

            # wait before telling oxtrust to find nginx container
            time.sleep(2)
            setup_obj.discover_nginx()
        except IndexError:
            pass


def notify_oxidp(ngx):
    with ngx.app.app_context():
        for oxidp in ngx.cluster.get_containers(type_="oxidp"):
            setup_obj = OxidpSetup(oxidp, ngx.cluster, ngx.app, ngx.logger)

            # wait before telling oxidp to find nginx container
            time.sleep(2)
            setup_obj.discover_nginx()


def notify_nginx(ox):
    """Notifies nginx to re-render virtual host and restart the process.
    """
    with ox.app.app_context():
        for nginx in ox.cluster.get_containers(type_="nginx"):
            setup_obj = NginxSetup(nginx, ox.cluster, ox.app, ox.logger)
            setup_obj.render_https_conf()
            setup_obj.restart_nginx()


def connect_setup_signals():
    ngx_setup_subscriber = signal("nginx_setup_completed")
    ngx_setup_subscriber.connect(notify_oxtrust)
    ngx_setup_subscriber.connect(notify_oxidp)

    ox_setup_subscriber = signal("ox_setup_completed")
    ox_setup_subscriber.connect(notify_nginx)


def connect_teardown_signals():
    ngx_teardown_subscriber = signal("nginx_teardown_completed")
    ngx_teardown_subscriber.connect(notify_oxtrust)
    ngx_teardown_subscriber.connect(notify_oxidp)

    ox_teardown_subscriber = signal("ox_teardown_completed")
    ox_teardown_subscriber.connect(notify_nginx)
