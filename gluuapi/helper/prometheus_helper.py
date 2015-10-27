# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from docker import Client
from jinja2 import Environment
from jinja2 import PackageLoader

from .weave_helper import WeaveHelper
from ..database import db


class PrometheusHelper(object):
    def __init__(self, app):
        try:
            self.cluster = db.all("clusters")[0]
        except IndexError:
            self.cluster = None

        try:
            self.provider = db.search_from_table(
                "providers",
                db.where("type") == "master",
            )[0]
        except IndexError:
            self.provider = None

        self.target_path = '/etc/gluu/prometheus/prometheus.yml'
        self.docker = Client("unix:///var/run/docker.sock")
        self.jinja_env = Environment(
            loader=PackageLoader("gluuapi", "templates")
        )
        self.app = app
        self.weave = WeaveHelper(self.provider, self.app)

    def __render(self):
        template = self.jinja_env.get_template("prometheus/prometheus.yml")
        rtxt = template.render(cluster=self.cluster)
        with open(self.target_path, 'w') as fp:
            fp.write(rtxt)

    def __restart(self):
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
