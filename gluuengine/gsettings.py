# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import multiprocessing
import os
import time

from .task import LicenseWatcherTask
from .utils import as_boolean


bind = ":8080"
workers = multiprocessing.cpu_count() * 2 + 1
threads = workers
worker_class = 'gthread'
loglevel = 'warning'
accesslog = '-'
errorlog = '-'
raw_env = 'API_ENV=prod'  # 'prod|test|dev'


def on_exit(server):
    app = server.app.load_wsgiapp()
    runfile = os.path.join(app.config["DATA_DIR"], "lwatcher.run")

    try:
        os.unlink(runfile)
    except OSError:
        pass


def post_fork(server, worker):
    # task is launched after a worker has been forked; as task is running
    # inside crochet/twisted reactor, we cannot use `when_ready` nor `pre_fork`
    # hook because, somehow, reactor seems unitialized in those hooks
    app = server.app.load_wsgiapp()
    runfile = os.path.join(app.config["DATA_DIR"], "lwatcher.run")

    if as_boolean(app.config["ENABLE_LICENSE"]):
        if not os.path.isfile(runfile):
            with open(runfile, "w") as fd:
                fd.write("1")

            app.logger.info("launching task on worker {}".format(worker))
            LicenseWatcherTask(app).perform_job()


def pre_fork(server, worker):
    # delay before forking other workers, this will give time for a worker
    # to claim task
    time.sleep(0.5)
