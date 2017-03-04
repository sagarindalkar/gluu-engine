# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import re
import os

from docker.tls import TLSConfig

from ..utils import po_run

LS_FIELDS = ["Name", "Active", "ActiveHost", "ActiveSwarm", "DriverName",
             "State", "URL", "Swarm", "Error", "DockerVersion", "ResponseTime"]
# GLUU_GET_DOCKER = 'https://raw.githubusercontent.com/GluuFederation/cluster-tools/master/get_docker.sh'
GLUU_GET_DOCKER = 'https://raw.githubusercontent.com/GluuFederation/cluster-tools/ce-3/get_docker.sh'

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
        cmd = " ".join([
            '--swarm-discovery=consul://{}:{}'.format(discovery.ip, discovery.port),
            '--engine-opt=cluster-store=consul://{}:{}'.format(discovery.ip, discovery.port),
            '--engine-opt=cluster-advertise=eth0:2376',
        ])
        return cmd

    def _get_generic_cmd(self, provider):
        cmd = " ".join([
            '--generic-ip-address={}'.format(provider.generic_ip_address),
            '--generic-ssh-key={}'.format(provider.generic_ssh_key),
            '--generic-ssh-user={}'.format(provider.generic_ssh_user),
            '--generic-ssh-port={}'.format(provider.generic_ssh_port),
        ])
        return cmd

    def _get_aws_cmd(self, provider):
        cmd = " ".join([
            '--amazonec2-access-key={}'.format(provider.amazonec2_access_key),
            '--amazonec2-secret-key={}'.format(provider.amazonec2_secret_key),
            '--amazonec2-ami={}'.format(provider.amazonec2_ami),
            '--amazonec2-instance-type={}'.format(provider.amazonec2_instance_type),
            '--amazonec2-region={}'.format(provider.amazonec2_region),
            '--amazonec2-private-address-only={}'.format(provider.amazonec2_private_address_only),
        ])
        return cmd

    def _get_do_cmd(self, provider):
        cmd = " ".join([
            '--digitalocean-access-token={}'.format(provider.digitalocean_access_token),
            '--digitalocean-size={}'.format(provider.digitalocean_size),
            '--digitalocean-image={}'.format(provider.digitalocean_image),
            '--digitalocean-region={}'.format(provider.digitalocean_region),
            '--digitalocean-backups={}'.format(provider.digitalocean_backups),
            '--digitalocean-private-networking={}'.format(provider.digitalocean_private_networking),
            '--digitalocean-ipv6={}'.format(provider.digitalocean_ipv6),
        ])
        return cmd

    def _get_rackspace_cmd(self, provider):
        pass

    def create(self, node, provider, discovery):
        cmd = [
            "create",
            "--driver={}".format(provider.driver),
            '--engine-install-url="{}"'.format(GLUU_GET_DOCKER),
        ]

        if provider.driver == 'generic':
            cmd.append(self._get_generic_cmd(provider))

        if provider.driver == 'amazonec2':
            cmd.append(self._get_aws_cmd(provider))

        if provider.driver == 'digitalocean':
            cmd.append(self._get_do_cmd(provider))

        if node.type == 'master':
            cmd.append('--swarm --swarm-master')
            cmd.append('--engine-label=org.gluu.node-type={}'.format(node.type))

        if node.type == 'worker':
            cmd.append('--swarm')
            cmd.append('--engine-label=org.gluu.node-type={}'.format(node.type))

        if node.type != 'discovery':
            cmd.append(self._dicovery(discovery))
            cmd.append('--engine-label=org.gluu.node-type={}'.format(node.type))

        cmd.append(node.name)
        cmd = " ".join(cmd)
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

    def ssh(self, machine_name, cmd=""):
        stdout = ""
        if cmd:
            cmd = 'ssh {} {}'.format(machine_name, cmd)
            stdout, stderr, error = self._run(cmd)
        return stdout.strip()

    def _scp(self, source, destination, recursive=False):
        r = '-r' if recursive else ''
        cmd = 'scp {} {} {}'.format(r, source, destination)
        self._run(cmd)
        return True

    def scp(self, source, destination, recursive=False):
        destination_machine_name = destination.split(':')[0]
        dest_tmp = '{}:/tmp'.format(destination_machine_name)
        #step one
        self._scp(source, dest_tmp, recursive)
        #step two
        r = '-r' if recursive else ''
        dest_path = ':'.join(destination.split(':')[1:])
        last_part = os.path.basename(source)
        source_tmp = '/tmp/{}'.format(last_part)
        cmd = 'sudo cp {} {} {}'.format(r, source_tmp, dest_path)
        self.ssh(destination_machine_name, cmd)

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

    def is_running(self, machine_name):
        cmd = 'ls -f {{.Name}} --filter state=running'
        stdout, _, _ = self._run(cmd)
        node_list = stdout.split('\n')
        return True if machine_name in node_list else False

    def list(self, state):
        cmd = 'ls -f {{.Name}} --filter state=%s' % state
        stdout, _, _ = self._run(cmd)
        node_list = stdout.split('\n')
        return node_list
