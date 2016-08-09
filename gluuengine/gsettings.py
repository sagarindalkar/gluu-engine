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
    try:
        os.unlink("/tmp/lwatcher.run")
    except OSError:
        pass
