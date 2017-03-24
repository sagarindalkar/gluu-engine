# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

from gluuengine.app import _application as app  # noqa

#to run
#gunicorn -w $(($(nproc)*2+1)) --threads $(($(nproc)*2+1)) -k gthread -b 127.0.0.1:8080 --log-level warning --access-logfile - --error-logfile - -e API_ENV=prod,LOG_DIR=/opt/gluulog,DATA_DIR=/opt/gluudata wsgi:app
