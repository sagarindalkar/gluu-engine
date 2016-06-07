# -*- coding: utf-8 -*-

import sys
import os
from itertools import cycle
from gluuengine.machine import Machine
from subprocess import Popen
from subprocess import PIPE
from distutils.dir_util import mkpath
from gluuengine.app import create_app
from gluuengine.database import db
import requests

def run(cmd_str, raise_error=True, env=None):
    cmd_list = cmd_str.strip().split()
    try:
        p = Popen(cmd_list, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        error_code = p.returncode
        pid = p.pid
        if raise_error and error_code:
            raise RuntimeError("return code {}: {}".format(error_code, stderr.strip()))
        return pid
    except OSError as exc:
        raise RuntimeError("return code {}: {}".format(exc.errno, exc.strerror))

def get_running_nodes():
    m = Machine()
    running_nodes = m.list('running')
    running_nodes.remove('gluu.discovery')
    return running_nodes

def request_container(port, node_id, container):
    requests.post('http://localhost:{}/containers/{}'.format(port, container), data = {'node_id':'{}'.format(node_id)})

if __name__ == '__main__':
    #validate
    if len(sys.argv) != 5:
        print 'arg missing'
        sys.exit(0)

    container_list = ['oxauth','oxidp']

    python_path = sys.argv[1]
    if not (os.path.exists(python_path) and os.path.isfile(python_path)):
        print 'bad python path'
        sys.exit(0)

    run_script_path = sys.argv[2]
    if not (os.path.exists(run_script_path) and os.path.isfile(run_script_path)):
        print 'bad run script path'
        sys.exit(0)

    container = sys.argv[3]
    deploy_size = int(sys.argv[4])

    if container not in container_list:
        print 'unsupported ox container'
        sys.exit(0)

    if not isinstance(deploy_size, (int, long) ):
        print 'deploy size is not int type'
        sys.exit(0)

    #make path
    home_dir = os.environ['HOME'] #because this script is linux only
    data_path = os.path.join(home_dir, "demo/gluudata")
    mkpath(data_path)
    log_path = os.path.join(home_dir, "demo/gluulog")
    mkpath(log_path)

    #set env
    env = os.environ.copy()
    env['LOG_DIR'] = log_path
    env['DATA_DIR'] = data_path

    #create gluu-engine processes
    for port in xrange(9080, 9080+deploy_size):
        cmd = '{} {}'.format(python_path, run_script_path)
        env['PORT'] = str(port)
        run(cmd_str=cmd, env=env)

    #get node ids of running nodes from DB
    running_nodes = get_running_nodes()
    running_nodes_ids = []

    # prepare Flask context
    app = create_app()

    with app.app_context():
        # nodes = db.search_from_table('nodes', ( (db.where("type") == 'master') | (db.where("type") == 'worker') ) )
        nodes = db.search_from_table("nodes", {"$or": [{"type": "master"}, {"type": "worker"}]})


    for node in nodes:
        running_nodes_ids.append(node.id)

    #start deploying container
    port_gen = (i for i in xrange(9080, 9080+deploy_size))
    node_id_pool = cycle(running_nodes_ids)

    for i in xrange(deploy_size):
            request_container(port_gen.next(), node_id_pool.next(), container)

    print '{} {} container will be deployed soon'.format(deploy_size, container)

#in terminal run this cmd to kill all gluu-engine processes
#$ ps ax | grep gluu-engine/run.py | grep -v grep | awk '{print $1}' | xargs kill
