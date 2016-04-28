# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import logging
import os

from crochet import run_in_reactor

from ..database import db
from ..machine import Machine


@run_in_reactor
def distribute_cluster_data(filepath):
    """Distributes cluster data to all consumer providers.

    :param filepath: Path to cluster database file.
    """
    mc = Machine()
    logger = logging.getLogger("gluuapi")

    # find all worker nodes where cluster database will be copied to
    worker_nodes = db.search_from_table(
        "nodes", db.where("type") == "worker",
    )
    for worker_node in worker_nodes:
        try:
            mc.ssh(worker_node.name, "mkdir -p {}".format(os.path.dirname(filepath)))
            mc.scp(filepath, "{}:{}".format(worker_node.name, filepath))
        except RuntimeError as exc:
            logger.warn(exc)
            logger.warn("something is wrong while copying {}".format(filepath))
