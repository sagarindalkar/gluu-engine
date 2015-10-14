# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path

from crochet import run_in_reactor

from .salt_helper import SaltHelper
from ..database import db


@run_in_reactor
def distribute_cluster_data(src):
    dest = src
    salt = SaltHelper()
    consumer_providers = db.search_from_table(
        "providers", db.where("type") == "consumer"
    )

    for provider in consumer_providers:
        salt.cmd(
            provider.hostname,
            "cmd.run",
            ["mkdir -p {}".format(os.path.dirname(dest))]
        )
        salt.copy_file(provider.hostname, src, dest)
