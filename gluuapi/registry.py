# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import ssl

REGISTRY_BASE_URL = "registry.gluu.org:5000"


def get_registry_cert(cert_fn):
    if not os.path.exists(cert_fn):
        cert = ssl.get_server_certificate(REGISTRY_BASE_URL.split(":"))
        with open(cert_fn, "w") as fn:
            parent_dir = os.path.dirname(cert_fn)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            fn.write(str(cert))
    return cert_fn
