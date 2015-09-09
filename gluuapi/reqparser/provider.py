# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re
from urllib import quote_plus

from flask import current_app
from marshmallow import validates
from marshmallow import post_load
from marshmallow import ValidationError
from docker.utils import parse_host
from docker.errors import DockerException

from ..extensions import ma

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')


class BaseProviderReq(ma.Schema):
    hostname = ma.Str(required=True)
    docker_base_url = ma.Str(required=True)
    ssl_cert = ma.Str(default="", missing="")
    ssl_key = ma.Str(default="", missing="")
    ca_cert = ma.Str(default="", missing="")

    @validates("hostname")
    def validate_hostname(self, value):
        # some provider like AWS uses dotted hostname,
        # e.g. ip-172-31-24-54.ec2.internal
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid:
            raise ValidationError("invalid hostname")

    @post_load
    def finalize_data(self, data):
        for field in ("ssl_cert", "ssl_key", "ca_cert"):
            # split lines but preserve the new-line special character
            lines = data[field].splitlines(True)
            for idx, line in enumerate(lines):
                # exclude first and last line
                if (idx == 0) or (idx == len(lines) - 1):
                    continue
                lines[idx] = quote_plus(line, safe="/+=\n")
            data[field] = "".join(lines)
        data["docker_cert_dir"] = current_app.config["DOCKER_CERT_DIR"]
        return data

    @validates("docker_base_url")
    def validate_docker_base_url(self, value):
        try:
            parse_host(value)
        except DockerException as exc:
            raise ValidationError(exc.message)

    @validates("ssl_cert")
    def validate_ssl_cert(self, value):
        base_url = self.context.get("docker_base_url", "")
        if base_url.startswith("https"):
            if not value:
                raise ValidationError("Field is required when "
                                      "'docker_base_url' uses https")

    @validates("ssl_key")
    def validate_ssl_key(self, value):
        base_url = self.context.get("docker_base_url", "")
        if base_url.startswith("https"):
            if not value:
                raise ValidationError("Field is required when "
                                      "'docker_base_url' uses https")

    @validates("ca_cert")
    def validate_ca_cert(self, value):
        base_url = self.context.get("docker_base_url", "")
        if base_url.startswith("https"):
            if not value:
                raise ValidationError("Field is required when "
                                      "'docker_base_url' uses https")


class ProviderReq(BaseProviderReq):
    type = ma.Select(choices=["master", "consumer"], required=True)


# backward-compat
EditProviderReq = BaseProviderReq
