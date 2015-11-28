# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import logging
import logging.config
import stat
import tempfile


def create_file_logger(filepath="", log_level=logging.DEBUG, name=""):
    """Create logger having FileHandler as its handler.

    :param filepath: Path to file (by default will use path generated
                     by ``tempfile.mkstemp`` function)
    :param log_level: Log level to use (by default uses ``DEBUG``)
    :param name: Logger name (by default will use current module name)
    """
    filepath = filepath or tempfile.mkstemp()[1]
    fp_dir = os.path.dirname(filepath)

    if not os.path.exists(fp_dir):
        os.makedirs(fp_dir)

    logger = logging.getLogger(name or __name__)
    logger.setLevel(log_level)
    ch = logging.FileHandler(filepath)
    ch.setLevel(log_level)
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s  - %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # set proper permission 644
    os.chmod(filepath,
             stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return logger


def configure_global_logging(logfile=None):  # pragma: no cover
    """Configure logging globally.
    """
    handlers = {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    }
    if logfile:
        handlers["file"] = {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": logfile,
            "mode": "a",
            "formatter": "simple",
        }

    log_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": handlers,
        "loggers": {
            "gluuapi": {
                "handlers": handlers.keys(),
                "propagate": True,
                "level": "INFO",
            },
            "werkzeug": {
                "handlers": handlers.keys(),
                "level": "INFO",
            },
            "twisted": {
                "handlers": handlers.keys(),
                "level": "ERROR",
            },
        },
    }
    logging.config.dictConfig(log_config)
