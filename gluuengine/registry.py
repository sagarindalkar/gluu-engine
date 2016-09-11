# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os
import subprocess

REGISTRY_BASE_URL = "registry.gluu.org:5000"


def get_registry_cert(cert_fn, redownload=False):
    if os.path.exists(cert_fn) and not redownload:
        return cert_fn

    ppn1 = subprocess.Popen(
        "echo -n".split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ppn2 = subprocess.Popen(
        "openssl s_client -connect {}".format(REGISTRY_BASE_URL).split(),
        stdin=ppn1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ppn3 = subprocess.Popen(
        ["sed", "-ne", r"/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p"],
        stdin=ppn2.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # receive SIGPIPE
    ppn1.stdout.close()
    ppn2.stdout.close()

    stdout, stderr = ppn3.communicate()
    retcode = ppn3.returncode

    if retcode != 0:
        raise RuntimeError("Failed to retrieve registry certificate; "
                           "reason={}".format(stderr.strip()))

    parent_dir = os.path.dirname(cert_fn)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    with open(cert_fn, "w") as fn:
        fn.write(stdout.strip())
    return cert_fn
