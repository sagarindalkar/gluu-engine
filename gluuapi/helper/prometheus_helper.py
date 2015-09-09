# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from jinja2 import Template
from docker import Client

from ..database import db

class PrometheusHelper(object):
    def __init__(self, template_dir):
        self.clusters = []
        self.template_dir = template_dir
        self.template = self.get_template_path('prometheus/prometheus.yml')
        self.target_path = '/etc/gluu/prometheus/prometheus.yml'
        self.docker = Client("unix:///var/run/docker.sock")

    def __load_clusters(self):
        self.clusters = db.all("clusters")

    def __render(self):
        with open(self.template, 'r') as fp:
            tmpl = fp.read()
        template = Template(tmpl)
        rtxt = template.render(clusters=self.clusters)
        with open(self.target_path, 'w') as fp:
            fp.write(rtxt)

    def __restart(self):
        self.docker.restart(container="prometheus")

    def update(self):
        self.__load_clusters()
        self.__render()
        self.__restart()

    def get_template_path(self, path):
        template_path = os.path.join(self.template_dir, path)
        return template_path
