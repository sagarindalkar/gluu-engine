# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import re

from docker.tls import TLSConfig

from ..utils import po_run

LS_FIELDS = ["Name", "Active", "ActiveHost", "ActiveSwarm", "DriverName",
             "State", "URL", "Swarm", "Error", "DockerVersion", "ResponseTime"]


class Machine(object):
    def __init__(self, path='docker-machine'):
        self.path = path

    def _run(self, cmd_str, raise_error=True):
        cmd = "{} {}".format(self.path, cmd_str)
        return po_run(cmd, raise_error)

    def _config(self, cmd, machine_name, docker_friendly):
        stdout, _, _ = self._run(cmd)
        config = stdout.strip()
        regexp = """(--tlsverify\n)?--tlscacert="(.+)"\n--tlscert="(.+)"\n--tlskey="(.+)"\n-H=(.+)"""
        match = re.match(regexp, config)
        tlsverify, tlscacert, tlscert, tlskey, host = match.group(1, 2, 3, 4, 5)
        tlsverify = bool(tlsverify)
        if docker_friendly:
            params = {
                'base_url': host.replace('tcp://', 'https://') if tlsverify else host,
                'tls': TLSConfig(
                    client_cert=(tlscert, tlskey),
                    ca_cert=tlscacert,
                    verify=True
                )
            }
        else:
            params = {
                'base_url': host.replace('tcp://', 'https://') if tlsverify else host,
                'tlscert': tlscert,
                'tlskey': tlskey,
                'tlscacert': tlscacert
            }
        return params

    def config(self, machine_name, docker_friendly=True):
        cmd = 'config {}'.format(machine_name)
        return self._config(cmd, machine_name, docker_friendly)

    # this method is only for swarm master
    def swarm_config(self, machine_name, docker_friendly=True):
        cmd = 'config --swarm {}'.format(machine_name)
        return self._config(cmd, machine_name, docker_friendly)

    def _dicovery(self, discovery):
        dlist = []
        dlist.append('--swarm-discovery=consul://{}:{}'.format(discovery.ip, discovery.port))
        dlist.append('--engine-opt=cluster-store=consul://{}:{}'.format(discovery.ip, discovery.port))
        dlist.append('--engine-opt=cluster-advertise=eth0:2376')
        return ' '.join(dlist)

    def _get_generic_cmd(self, discovery, provider, node):
        clist = []
        clist.append('create')
        clist.append('--driver {}'.format(provider.driver))
        clist.append('--generic-ip-address={}'.format(
            provider.generic_ip_address))
        clist.append(
            '--generic-ssh-key={}'.format(provider.generic_ssh_key))
        clist.append('--generic-ssh-user={}'.format(
            provider.generic_ssh_user))
        clist.append('--generic-ssh-port={}'.format(
            provider.generic_ssh_port))

        if node.type == 'master':
            clist.append('--swarm --swarm-master')

        if node.type == 'worker':
            clist.append('--swarm')

        if node.type != 'discovery':
            clist.append(self._dicovery(discovery))

        clist.append('{}'.format(node.name))
        cmd = ' '.join(clist)
        return cmd

    def _get_aws_cmd(self, discovery, provider, node):
        clist = []
        clist.append('create')
        clist.append('--driver {}'.format(provider.driver))
        clist.append('--amazonec2-access-key={}'.format(
            provider.amazonec2_access_key))
        clist.append(
            '--amazonec2-secret-key={}'.format(provider.amazonec2_secret_key))
        clist.append('--amazonec2-ami={}'.format(
            provider.amazonec2_ami))
        clist.append('--amazonec2-instance-type={}'.format(
            provider.amazonec2_instance_type))
        clist.append('--amazonec2-region={}'.format(
            provider.amazonec2_region))

        if node.type == 'master':
            clist.append('--swarm --swarm-master')

        if node.type == 'worker':
            clist.append('--swarm')

        if node.type != 'discovery':
            clist.append(self._dicovery(discovery))

        clist.append('{}'.format(node.name))
        cmd = ' '.join(clist)
        return cmd

    def _get_do_cmd(self, discovery, provider, node):
        clist = []
        clist.append('create')
        clist.append('--driver {}'.format(provider.driver))
        clist.append('--digitalocean-access-token={}'.format(
            provider.digitalocean_access_token))
        clist.append(
            '--digitalocean-size={}'.format(provider.digitalocean_size))
        clist.append('--digitalocean-image={}'.format(
            provider.digitalocean_image))

        if node.type == 'master':
            clist.append('--swarm --swarm-master')

        if node.type == 'worker':
            clist.append('--swarm')

        if node.type != 'discovery':
            clist.append(self._dicovery(discovery))

        clist.append('{}'.format(node.name))
        cmd = ' '.join(clist)
        return cmd

    def create(self, node, provider, discovery):
        if provider.driver == 'generic':
            cmd = self._get_generic_cmd(discovery, provider, node)

        if provider.driver == 'amazonec2':
            cmd = self._get_aws_cmd(discovery, provider, node)

        if provider.driver == 'digitalocean':
            cmd = self._get_do_cmd(discovery, provider, node)

        self._run(cmd)
        return True

    def inspect(self, machine_name):
        cmd = 'inspect {}'.format(machine_name)
        stdout, _, _ = self._run(cmd)
        return json.loads(stdout.strip())

    def ip(self, machine_name):
        cmd = 'ip {}'.format(machine_name)
        stdout, _, _ = self._run(cmd)
        return stdout.strip()
        # bellow is a alternate way to suppress exception and provide error msg
        #stdout, stderr, error = self._run(cmd, raise_error=False)
        #if not error:
        #    return stdout.strip()
        #else:
        #    return {'error_code': error, 'msg': stderr}

    def kill(self, machine_name):
        cmd = 'kill {}'.format(machine_name)
        self._run(cmd)
        return True

    def ls(self):
        seperator = "|"
        fields = seperator.join(["{{.%s}}" % i for i in LS_FIELDS])
        cmd = 'ls -f ' + fields
        stdout, stderr, errorcode = self._run(cmd)
        machines = []
        for line in stdout.split("\n"):
            machine = {LS_FIELDS[index]: value for index, value in enumerate(line.split(seperator))}
            machines.append(machine)
        return machines

    def provision(self, machine_name):
        cmd = 'provision {}'.format(machine_name)
        self._run(cmd)
        return True

    def regenerate_certs(self, machine_name):
        cmd = 'regenerate-certs -f {}'.format(machine_name)
        self._run(cmd)
        return True

    def restart(self, machine_name):
        cmd = 'restart {}'.format(machine_name)
        self._run(cmd)
        return True

    def rm(self, machine_name, force=False):
        f = '-f' if force else ''
        cmd = 'rm -y {} {}'.format(f, machine_name)
        self._run(cmd)
        return True

    def ssh(self, machine_name, cmd):
        if cmd:
            cmd = 'ssh {} {}'.format(machine_name, cmd)
            stdout, stderr, error = self._run(cmd)
        return stdout.strip()

    def scp(self, source, destination, recursive=False):
        r = '-r' if recursive else ''
        cmd = 'scp {} {} {}'.format(r, source, destination)
        self._run(cmd)
        return True

    def status(self, machine_name):
        cmd = 'status {}'.format(machine_name)
        stdout, _, _ = self._run(cmd)
        return stdout.strip() == 'Running'

    def start(self, machine_name):
        cmd = 'start {}'.format(machine_name)
        self._run(cmd)
        return True

    def stop(self, machine_name):
        cmd = 'stop {}'.format(machine_name)
        self._run(cmd)
        return True

    def upgrade(self, machine_name):
        cmd = 'upgrade {}'.format(machine_name)
        self._run(cmd)
        return True

    def url(self, machine_name):
        cmd = 'url {}'.format(machine_name)
        stdout, _, _ = self._run(cmd)
        return stdout.strip()

    def version(self):
        regexp = "docker-machine version (.+), build (.+)"
        cmd = 'version'
        stdout, _, _ = self._run(cmd)
        version_str = stdout.strip()
        match = re.match(regexp, version_str)
        if not match:
            raise RuntimeError("can't parse output (\"%s\")" % version_str)
        return match.group(1)
