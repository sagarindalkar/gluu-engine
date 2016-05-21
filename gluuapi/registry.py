# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import ssl

REGISTRY_BASE_URL = "registry.gluu.org:5000"
#REGISTRY_BASE_URL = "registry.gluu.org"
#PORT = 5000
#TODO: need to fix it !? (ssl.SSLError: [Errno 1] _ssl.c:510: error:1408F10B:SSL routines:SSL3_GET_RECORD:wrong version number)
def get_registry_cert(cert_fn):
    if not os.path.exists(cert_fn):
        cert = ssl.get_server_certificate(REGISTRY_BASE_URL.split(":"))
        #cert = ssl.get_server_certificate((REGISTRY_BASE_URL,PORT))
        with open(cert_fn, "w") as fn:
            parent_dir = os.path.dirname(cert_fn)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            fn.write(str(cert))
    return cert_fn
