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
import logging
import sys
import time

from gluuapi.helper import SaltHelper
from gluuapi.helper import DockerHelper
from gluuapi.helper import WeaveHelper
from gluuapi.database import db
from gluuapi.setup import LdapSetup
from gluuapi.setup import OxauthSetup
from gluuapi.setup import OxtrustSetup
from gluuapi.setup import HttpdSetup


class RecoverProviderTask(object):
    def __init__(self, app, provider_id, exec_delay=30):
        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__,
        )
        self.app = app
        self.exec_delay = exec_delay

        self.provider = db.get(provider_id, "providers")
        if not self.provider:
            self.logger.error("invalid provider")
            sys.exit(1)

        self.docker = DockerHelper(self.provider, logger=self.logger)
        self.salt = SaltHelper()

        self.cluster = db.all("clusters")[0]
        self.weave = WeaveHelper(self.provider,
                                 self.cluster,
                                 self.app.config["SALT_MASTER_IPADDR"],
                                 logger=self.logger)

    def perform_job(self):
        self.logger.info("trying to recover provider {}".format(self.provider.id))

        self.logger.info("inspecting weave container")
        if self.container_stopped("weave"):
            self.logger.warn("weave container is not running")
            self.relaunch_weave()

        nodes = sorted(self.provider.get_node_objects(),
                       key=lambda node: node.recovery_priority)

        for node in nodes:
            self.check_node(node)

        if self.provider.type == "master":
            self.logger.info("inspecting prometheus container")
            if self.container_stopped("prometheus"):
                self.logger.warn("prometheus container is not running")
                self.relaunch_prometheus()

    def relaunch_weave(self):
        self.weave.launch(register_minion=False)

    def relaunch_prometheus(self):
        self.logger.info("restarting prometheus")
        prom_cmd = "docker start prometheus"
        self.salt.cmd(self.provider.hostname, "cmd.run", [prom_cmd])

        # needed by Prometheus helper
        with open("/var/run/prometheus.cid", "w") as fp:
            fp.write(self.docker.inspect_container("prometheus")["Id"])

    def check_node(self, node):
        self.logger.info("inspecting {} node {}".format(node.type, node.id))
        if self.container_stopped(node.id):
            self.logger.warn("{} node {} is not running".format(node.type, node.id))
            self.recover_node(node)

    def recover_node(self, node):
        self.logger.info("re-running {} node {}".format(node.type, node.id))
        self.docker.start_container(node.id)

        self.logger.info("attaching weave IP")
        attach_cmd = "weave attach {}/{} {}".format(
            node.weave_ip, self.cluster.prefixlen, node.id,
        )
        self.salt.cmd(self.provider.hostname, "cmd.run", [attach_cmd])

        # delay to prepare minion inside container
        time.sleep(float(self.exec_delay))

        node.ip = self.docker.get_container_ip(node.id)
        db.update(node.id, node, "nodes")
        self.node_setup(node)

    def node_setup(self, node):
        template_dir = self.app.config["TEMPLATES_DIR"]

        self.logger.info("running entrypoint for "
                         "{} node {}".format(node.type, node.id))

        if node.type == "ldap":
            setup_obj = LdapSetup(node, self.cluster,
                                  self.logger, template_dir)
            setup_obj.start_opendj()

        elif node.type == "oxauth":
            setup_obj = OxauthSetup(node, self.cluster,
                                    self.logger, template_dir)
            setup_obj.start_tomcat()
            for ldap in self.cluster.get_ldap_objects():
                setup_obj.add_ldap_host_entry(ldap)

        elif node.type == "oxtrust":
            setup_obj = OxtrustSetup(node, self.cluster,
                                     self.logger, template_dir)
            setup_obj.render_server_xml_template()
            setup_obj.start_tomcat()
            setup_obj.discover_httpd()
            for ldap in self.cluster.get_ldap_objects():
                setup_obj.add_ldap_host_entry(ldap)

        elif node.type == "httpd":
            setup_obj = HttpdSetup(node, self.cluster,
                                   self.logger, template_dir)
            setup_obj.remove_pidfile()
            setup_obj.start_httpd()

            # clear iptables rule for this node
            setup_obj.remove_iptables_rule()
            setup_obj.add_iptables_rule()

    def container_stopped(self, cid):
        meta = self.docker.inspect_container(cid)
        return not meta["State"]["Running"]
