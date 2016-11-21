# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import json
import logging
import os
import tempfile

from crochet import run_in_reactor

from ..database import db
from ..machine import Machine


@run_in_reactor
def distribute_shared_database(app, node):
    """Distributes cluster data to specific node.

    :param app: An instance of :class:`flask.Flask`.
    """
    mc = Machine()
    logger = logging.getLogger("gluuengine")
    filepath = app.config["SHARED_DATABASE_URI"]

    clusters = db.all("clusters")

    if not clusters:
        logger.warn("cluster is currently unavailable")
        return

    containers = db.search_from_table(
        "containers",
        {"node_id": node.id},
    )

    data = {}
    data["clusters"] = {1: clusters[0].as_dict()}
    data["nodes"] = {1: node.as_dict()}
    data["containers"] = {
        idx: container.as_dict()
        for idx, container in enumerate(containers, 1)
    }

    with tempfile.NamedTemporaryFile() as src:
        src.write(json.dumps(data))
        src.seek(0)

        try:
            mc.ssh(
                node.name,
                "mkdir -p {}".format(os.path.dirname(filepath))
            )
            mc.scp(src.name, "{}:{}".format(node.name, filepath))
        except RuntimeError as exc:
            logger.warn("something is wrong while copying {}; "
                        "reason={}".format(filepath, exc))


# backward-compat
distribute_cluster_data = distribute_shared_database
