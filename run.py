#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from crochet import setup as crochet_setup

from gluuapi.app import create_app
from gluuapi.settings import DevConfig, ProdConfig

if os.environ.get("API_ENV") == 'prod':
    app = create_app(ProdConfig)
else:
    app = create_app(DevConfig)

if not os.environ.get("SALT_MASTER_IPADDR"):
    raise SystemExit("Unable to get salt-master IP address. "
                     "Make sure the SALT_MASTER_IPADDR "
                     "environment variable is set.")


if __name__ == '__main__':
    crochet_setup()
    app.run(host='0.0.0.0', port=app.config['PORT'])
