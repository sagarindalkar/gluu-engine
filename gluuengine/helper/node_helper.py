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
def distribute_shared_database(filepath, app):
    """Distributes cluster data to all consumer providers.

    :param filepath: Path to shared database file.
    """
    mc = Machine()
    logger = logging.getLogger("gluuengine")

    with app.app_context():
        src = dest = db.export_as_json(filepath)

        # find all nodes where shared database will be copied to
        nodes = db.all("nodes")
        for node in nodes:
            try:
                mc.ssh(node.name,
                       "mkdir -p {}".format(os.path.dirname(dest)))
                mc.scp(src, "{}:{}".format(node.name, dest))
            except RuntimeError as exc:
                logger.warn(exc)
                logger.warn("something is wrong while copying {}".format(src))


# backward-compat
distribute_cluster_data = distribute_shared_database
