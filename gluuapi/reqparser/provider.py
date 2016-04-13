# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import re

from marshmallow import validates
from marshmallow import ValidationError
from marshmallow.validate import OneOf
from docker.utils import parse_host
from docker.errors import DockerException

from ..extensions import ma
from ..database import db

# regex pattern for hostname as defined by RFC 952 and RFC 1123
HOSTNAME_RE = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')

PROVIDER_CHOICES = ("master", "consumer",)


class BaseProviderReq(ma.Schema):
    hostname = ma.Str(required=True)
    docker_base_url = ma.Str(required=True)
    connect_delay = ma.Int(default=10, missing=10,
                           error="must use numerical value")
    exec_delay = ma.Int(default=15, missing=15,
                        error="must use numerical value")

    @validates("hostname")
    def validate_hostname(self, value):
        """Validates provider's hostname.

        :param value: Provider's hostname.
        """
        # some provider like AWS uses dotted hostname,
        # e.g. ip-172-31-24-54.ec2.internal
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid:
            raise ValidationError("invalid hostname")

        # ensure hostname is unique (not taken by existing providers)
        hostname_num = db.count_from_table(
            "providers",
            db.where("hostname") == value,
        )
        if hostname_num:
            raise ValidationError("hostname has been taken by "
                                  "existing provider")

    @validates("docker_base_url")
    def validate_docker_base_url(self, value):
        """Validates provider's docker URL.

        :param value: URL to docker Remote API.
        """
        # enforce value to use `unix` or `https` prefix
        if not any([value.startswith("unix"), value.startswith("https")]):
            raise ValidationError("Must use unix or https prefix")

        try:
            # check whether value is supported by docker
            parse_host(value)
        except DockerException as exc:
            raise ValidationError(exc.message)


class ProviderReq(BaseProviderReq):
    type = ma.Str(validate=OneOf(PROVIDER_CHOICES))

    cluster_id = ma.Str(required=True)

    @validates("cluster_id")
    def validate_cluster(self, value):
        """Validates cluster's ID.

        :param value: ID of the cluster.
        """
        cluster = db.get(value, "clusters")
        self.context["cluster"] = cluster
        if not cluster:
            raise ValidationError("invalid cluster ID")


class EditProviderReq(BaseProviderReq):
    @validates("hostname")
    def validate_hostname(self, value):
        """Validates provider's hostname.

        :param value: Provider's hostname.
        """
        provider = self.context.get("provider")

        # some provider like AWS uses dotted hostname,
        # e.g. ip-172-31-24-54.ec2.internal
        valid = all(HOSTNAME_RE.match(v) for v in value.split("."))
        if not valid:
            raise ValidationError("invalid hostname")

        if provider:
            # ensure hostname is unique (not taken by another provider)
            hostname_num = db.count_from_table(
                "providers",
                (db.where("hostname") == value) & (db.where("id") != provider.id),
            )
            if hostname_num:
                raise ValidationError("hostname has been taken by "
                                      "existing provider")
