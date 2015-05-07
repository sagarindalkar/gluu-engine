# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from gluuapi.database import db
from jinja2 import Template
from docker import Client

class PrometheusHelper(object):
    def __init__(self):
        self.clusters = []
        self.template = 'gluuapi/templates/prometheus/prometheus.conf.tmpl'
        self.target_path = '/etc/gluu/prometheus/prometheus.conf' #TODO: must come from flask config
        self.docker = Client("unix:///var/run/docker.sock")
        self.prometheus_cid = "/var/run/prometheus.cid"

    def __load_clusters(self):
        self.clusters = db.all("clusters")

    def __render(self):
        with open(self.template, 'r') as fp:
            tmpl = fp.read()
        template = Template(tmpl)
        rtxt = template.render(clusters = self.clusters)
        with open(self.target_path, 'w') as fp:
            fp.write(rtxt)

    def __restart(self):
        with open(self.prometheus_cid, 'r') as fp:
            cid = fp.read()
        self.docker.restart(container=cid)

    def update(self):
        self.__load_clusters()
        self.__render()
        self.__restart()
