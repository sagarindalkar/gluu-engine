# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import multiprocessing
import os


bind = ":8080"
workers = multiprocessing.cpu_count() * 2 + 1
threads = workers
worker_class = 'gthread'
loglevel = 'warning'
accesslog = '-'
errorlog = '-'
raw_env = 'API_ENV=prod'  # 'prod|test|dev'


def on_exit(server):
    wsgi_app = server.app.load_wsgiapp()
    runfile = os.path.join(wsgi_app.config["DATA_DIR"], "lwatcher.run")

    try:
        os.unlink(runfile)
    except OSError:
        pass
