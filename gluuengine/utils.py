# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import base64
import hashlib
import json
import os
import random
import string
import sys
import tarfile
import tempfile
import traceback
import uuid
from subprocess import Popen
from subprocess import PIPE

import requests
from M2Crypto.EVP import Cipher

# Default charset
_DEFAULT_CHARS = "".join([string.ascii_uppercase,
                          string.digits,
                          string.lowercase])


def get_random_chars(size=12, chars=_DEFAULT_CHARS):
    """Generates random characters.
    """
    return ''.join(random.choice(chars) for _ in range(size))


def ldap_encode(password):
    # borrowed from community-edition-setup project
    # see http://git.io/vIRex
    salt = os.urandom(4)
    sha = hashlib.sha1(password)
    sha.update(salt)
    b64encoded = '{0}{1}'.format(sha.digest(), salt).encode('base64').strip()
    encrypted_password = '{{SSHA}}{0}'.format(b64encoded)
    return encrypted_password


def get_quad():
    # borrowed from community-edition-setup project
    # see http://git.io/he1p
    return str(uuid.uuid4())[:4].upper()


def generate_passkey():
    return "".join([get_random_chars(), get_random_chars()])


def encrypt_text(text, key):
    # Porting from pyDes-based encryption (see http://git.io/htxa)
    # to use M2Crypto instead (see https://gist.github.com/mrluanma/917014)
    cipher = Cipher(alg="des_ede3_ecb", key=b"{}".format(key), op=1, iv="\0" * 16)
    encrypted_text = cipher.update(b"{}".format(text))
    encrypted_text += cipher.final()
    return base64.b64encode(encrypted_text)


def decrypt_text(encrypted_text, key):
    # Porting from pyDes-based encryption (see http://git.io/htpk)
    # to use M2Crypto instead (see https://gist.github.com/mrluanma/917014)
    cipher = Cipher(alg="des_ede3_ecb", key=b"{}".format(key), op=0, iv="\0" * 16)
    decrypted_text = cipher.update(base64.b64decode(b"{}".format(encrypted_text)))
    decrypted_text += cipher.final()
    return decrypted_text


def exc_traceback():
    """Get exception traceback as string.
    """
    exc_info = sys.exc_info()
    exc_string = ''.join(
        traceback.format_exception_only(*exc_info[:2]) +
        traceback.format_exception(*exc_info))
    return exc_string


def decode_signed_license(signed_license, public_key,
                          public_password, license_password):
    """Gets license's metadata from a signed license retrieved from license
    server (https://license.gluu.org).

    :param signed_license: Signed license retrieved from license server
    :param public_key: Public key retrieved from license server
    :param public_password: Public password retrieved from license server
    :param license_password: License password retrieved from license server
    """
    validator = os.environ.get(
        "OXLICENSE_VALIDATOR",
        "/usr/share/oxlicense-validator/oxlicense-validator.jar",
    )

    product = "de"
    current_date = retrieve_current_date()
    stdout, _, _ = po_run("java -jar {} {} {} {} {} {} {}".format(
        validator,
        signed_license,
        public_key,
        public_password,
        license_password,
        product,
        current_date,
    ))

    # output example:
    #
    #   Validator expects: java org.xdi.oxd.license.validator.LicenseValidator
    #   {"valid":true,"metadata":{}}
    #
    # but we only care about the last line
    meta = stdout.splitlines()[-1]

    decoded_license = json.loads(meta)
    return decoded_license


def retrieve_signed_license(code):
    """Retrieves signed license from https://license.gluu.org.

    :param code: Code (or licenseId).
    """
    mac_addr = get_mac_addr()
    resp = requests.post(
        "https://license.gluu.org/oxLicense/rest/generate",
        data={
            "licenseId": code,
            "count": 1,
            "macAddress": mac_addr,
        },
        verify=False,
    )
    return resp


def reindent(text, num_spaces):
    text = [(num_spaces * " ") + line.lstrip() for line in text.splitlines()]
    text = "\n".join(text)
    return text


def generate_base64_contents(text, num_spaces):
    text = text.encode("base64").strip()
    if num_spaces:
        text = reindent(text, 1)
    return text


def generate_base64_from_file(filename, num_spaces):
    text = ""
    with open(filename) as fd:
        text = fd.read()
    return generate_base64_contents(text, num_spaces)


def get_sys_random_chars(size=12, chars=_DEFAULT_CHARS):
    """Generates random characters based on OS.
    """
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))


def po_run(cmd_str, raise_error=True):
    cmd_list = cmd_str.strip().split()

    try:
        p = Popen(cmd_list, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        error_code = p.returncode

        if raise_error and error_code:
            raise RuntimeError("return code {}: {}".format(error_code, stderr.strip()))
        return stdout.strip(), stderr.strip(), error_code
    except OSError as exc:
        raise RuntimeError("return code {}: {}".format(exc.errno, exc.strerror))


def as_boolean(val, default=False):
    truthy = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
    falsy = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))

    if val in truthy:
        return True
    if val in falsy:
        return False
    return default


def make_tarfile(src):
    abspath = os.path.abspath(src)
    recursive = os.path.isdir(abspath)

    fd = tempfile.NamedTemporaryFile()
    tf = tarfile.open(mode="w", fileobj=fd)
    tf.add(abspath, arcname=os.path.basename(src), recursive=recursive)
    tf.close()
    fd.seek(0)
    return fd


def extract_tarfile(tardata, path):
    with tarfile.open(mode='r', fileobj=tardata) as t:
        t.extractall(path)


def retrieve_current_date():
    """Retrieves current date from license server.
    """
    req = requests.get(
        "https://license.gluu.org/oxLicense/rest/currentMilliseconds"
    )
    return req.json()


def get_mac_addr():
    """Gets MAC address according to standard IEEE EUI-48 format.
    """
    mac_num = hex(uuid.getnode()).replace("0x", "").upper()
    return "-".join(mac_num[i:i + 2] for i in range(0, 11, 2))


def populate_license(license_key):
    err = ""

    resp = retrieve_signed_license(license_key.code)
    if not resp.ok:
        err = "unable to retrieve license from license server; " \
              "code={} reason={}".format(resp.status_code, resp.reason)
        return license_key, err

    signed_license = resp.json()[0]["license"]
    try:
        # generate metadata
        decoded_license = decode_signed_license(
            signed_license,
            license_key.decrypted_public_key,
            license_key.decrypted_public_password,
            license_key.decrypted_license_password,
        )
    except ValueError as exc:
        err = "unable to validate license key; reason={}".format(exc)
        decoded_license = {"valid": False, "metadata": {}}
    finally:
        license_key.signed_license = signed_license
        license_key.valid = decoded_license["valid"]
        # setting metadata directly will raise error on value conversion,
        # hence we're importing the data
        # license_key.metadata.import_data(decoded_license["metadata"])
        license_key._metadata = decoded_license["metadata"]
        return license_key, err
