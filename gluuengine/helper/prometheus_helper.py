# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging

from docker import Client
from jinja2 import Environment
from jinja2 import PackageLoader

from ..weave import Weave
from ..database import db


class PrometheusHelper(object):
    def __init__(self, app, logger=None):
        self.app = app

        # with self.app.app_context():
        try:
            self.cluster = db.all("clusters")[0]
        except IndexError:
            self.cluster = None

        try:
            self.provider = db.search_from_table(
                "providers",
                {"type": "master"},
            )[0]
        except IndexError:
            self.provider = None

        self.target_path = '/etc/gluu/prometheus/prometheus.yml'
        self.docker = Client("unix:///var/run/docker.sock")
        self.jinja_env = Environment(
            loader=PackageLoader("gluuengine", "templates")
        )
        self.logger = logger or logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.weave = Weave(self.provider, self.app, logger=self.logger)

    def __render(self):
        """Copies rendered jinja template.
        """
        template = self.jinja_env.get_template("prometheus/prometheus.yml")
        rtxt = template.render(cluster=self.cluster)
        with open(self.target_path, 'w') as fp:
            fp.write(rtxt)

    def __restart(self):
        """Restarts the container.
        """
        self.docker.restart(container="prometheus")

    def update(self):
        self.__render()
        self.__restart()

        # attach weave IP for prometheus container
        # so prometheus can scrape all metrics from all
        # nodes
        if all([self.cluster, self.provider]):
            addr, prefixlen = self.cluster.prometheus_weave_ip
            cidr = "{}/{}".format(addr, prefixlen)
            self.weave.attach(cidr, "prometheus")
