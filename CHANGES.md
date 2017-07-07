# Changelog

Here you can see the full list of changes between each `gluu-engine` release.

## Version 0.7.0-beta2

Released on July 8th, 2017.

* Fixed module imports.

## Version 0.7.0-beta1

Released on July 7th, 2017.

* Added experimental support for CE 3.0.1 (breaking changes).

## Version 0.6.4

Released on March 16th, 2017.

* Added missing `dataset` package.

## Version 0.6.3

Released on March 15th, 2017.

* Added `dataset` wrapper to replace missing Flask-Dataset extension (no longer available in public repository). Related issue: [#113](https://github.com/GluuFederation/gluu-engine/issues/113).

## Version 0.6.2

Released on February 28th, 2017.

* Fixed incorrect query to search discovery node.

## Version 0.6.1

Released on December 30th, 2016.

* Added volume for oxTrust logs in master node.

## Version 0.6.0

Released on December 13th, 2016.

* Added experimental support for MySQL (an alternative to MongoDB).

## Version 0.5.9

Released on November 4th, 2016.

* Added auto-update check to determine whether license need to be updated or not.

## Version 0.5.8

Released on October 26th, 2016.

* `pre_fork` delay time has been increased.
* Sensitive fields are hidden from API responses.
* Added command to distribute SSL certificate and key.
* Added new rule to validate `active` flag in license's metadata. Related issue: [#103](https://github.com/GluuFederation/gluu-engine/issues/103).

## Version 0.5.7

Released on October 17th, 2016.

* Fixed task launcher being running in each gunicorn worker. Related issue: [#101](https://github.com/GluuFederation/gluu-engine/issues/101).

## Version 0.5.6

Released on October 13th, 2016.

* Updated `oxauth-config.json` template.
* Updated `gluu_https.conf` template for `gluunginx` container.
* Smaller entries in `shared.json`.
* Reuse same SSL certs and keys for web frontends.

## Version 0.5.5

Released on September 19th, 2016.

* Fixed error when having connection problem to license server.

## Version 0.5.4

Released on September 16th, 2016.

* Updated license enforcement and retries.

## Version 0.5.3

Released on September 11th, 2016.

* Simplified containers resolver using weave dns load balancer.

## Version 0.5.2

Released on September 2nd, 2016.

* Simplified containers resolver using weave dns load balancer.

## Version 0.5.1

Released on August 31st, 2016.

* Use newest `oxlicense-validator.jar` to validate license.
* Fixed race condition in `Docker.copy_to_container` method when generating random temporary directory.

## Version 0.5.0

Released on August 29th, 2016.

WARNING: this release is a non-backward compatible with older releases.

*   New terms are introduced and some old terms are modified:

    * Cluster and LicenseKey remain intact.
    * The old Provider is renamed to Node; the new Provider refers to cloud/service name.
    * The old Node is renamed to Container; the new Node refers to actual machine/server.
    * The old NodeLog is renamed to ContainerLog

*   Image changes:

    * `gluuoxauth` upgraded to CE v2.4.4.
    * `gluuoxtrust` upgraded to CE v2.4.4.
    * `gluuopendj` upgraded to OpenDJ 3 (Gluu snapshot).
    * `gluuhttpd` removed from cluster.
    * `gluuoxidp` is no longer supported.

*   Fixed error when stopping failed container deployment.
*   Speed up container teardown by skipping provisioning in failed container.
*   Set maximum file descriptor in `ldap` container.
*   Docker Engine is upgraded to v1.11.2.
*   Speed up image downloads/updates by pulling them from Gluu's private registry.
*   Removed `X-Deploy-Log` header from Container API response in favor of `X-Container-Setup-Log`
*   Introduced `X-Container-Teardown-Log` header.
*   Removed unused `gluuengine distribute-data`, `gluuengine populate-node-logs`, and `runserver` commands.
*   Fixed license key monitoring daemon.
*   oxTrust is exposed as part of the cluster.
*   Fixed nginx config.
*   Fixed issue with expired registry cert.

## Version 0.4.4

Released on February 26th, 2016.

* Added URL to setup and teardown log in Node Log. Related issue: [#73](https://github.com/GluuFederation/gluu-flask/issues/73).

## Version 0.4.3

Released on February 25th, 2016.

* Fixed blocking node deletion process. Related issue: [#69](https://github.com/GluuFederation/gluu-flask/issues/69).
* Added NodeLog API.

## Version 0.4.2

Released on January 12th, 2016.

* Added callbacks to handle inotify ``MOVED_TO``, ``ATTRIB``, and ``IN_CLOSE_WRITE`` events in OxidpWatcherTask.
* Use timed rotating log file instead of plain log file.
* Fixed bug in Provider model where state is bypassed.
* Added LDAP config to reject unauthenticated requests.
* Added log file for memcached process inside oxIdp node.
* Use ``sticky`` directive (if available) when load balancing oxIdp nodes.
* Fixed oxIdp cluster setup. Related issue: [#53](https://github.com/GluuFederation/gluu-flask/issues/53).
* Added 2048-bit Diffie Helmann Group in nginx node to prevent LogJam attack.
* Added JSF salt for oxauth node.
* Use ``sticky`` directive when load balancing oxAuth nodes.
* Removed `license_count_limit` policy.
* On failed deployment, node/container is stopped instead of removed from cluster.
* Added feature to use non self-signed SSL certificates. Related issue: [#56](https://github.com/GluuFederation/gluu-flask/issues/56).
* Added feature to convert SSL pem-based to der-based format certificate. Related issue: [#56](https://github.com/GluuFederation/gluu-flask/issues/56).
* Fixed I/O error in VM with low-resource. Related issue: [#58](https://github.com/GluuFederation/gluu-flask/issues/58).

## Version 0.4.1

Released on November 28th, 2015.

* docker is upgraded to v1.8.3.
* Automated import on docker certificates required for making request to docker Remote API. Related issue: [#50](https://github.com/GluuFederation/gluu-flask/issues/50).
* tinydb is upgraded to v3.0.0.
* `gluuoxauth` image is updated to use oxAuth v2.4.1.
* `gluuoxidp` image is updated to use oxIdp v2.4.1.
* `gluuoxtrust` image is updated to use oxTrust v2.4.1.
* `gluuopendj` image is updated to use latest `oxauth-model` and `oxauth-server` JAR files.

## Version 0.4.0

Released on November 13th, 2015.

* Added new `gluuoxidp` docker image based on oxIDP v2.4.0.
* Added new `oxidp` node (docker container for gluuoxidp).
* Added background task (`gluuapi.task.fswatcher.OxidpWatcherTask`) to monitor and distribute schema and metadata for `oxidp` node.
* Added new `gluunginx` docker image.
* Added new `nginx` node (docker container for gluunginx).
* `httpd` node is deprecated in favor of `nginx` node.
* License expiration task is now monitoring `oxidp` node as well.
* `weave` is upgraded to v1.1.0.
* `prometheus` container is attached to the weave network due to changes in weave (since v0.11.0).
* Introduced local DNS server using weaveDNS.
* Swagger UI is removed.
* Added salt event handler to catch errors in some deployment tasks.
* Moved templates from `gluuapi/templates/salt` to `gluuapi/templates/nodes`.
* Enforced `docker_base_url` value to use either `unix` or `https` prefix. Related issue: [#42](https://github.com/GluuFederation/gluu-flask/issues/42).
* `force` option in Node API is renamed to `force_rm`.
* Fixed missing `/var/ox` directory and its subdirectories in oxtrust node.
* Add validation rule to ensure provider's hostname is unique.
* Fixed validation rule in Node API caused by missing `node_type` parameter.
* Added support to import custom schema for LDAP. Related issue: [#38](https://github.com/GluuFederation/gluu-flask/issues/38).
* Fixed issue in OxidpWatcherTask where cluster object is not refreshed.
* Cluster data are distributed after enabling/disabling consumer provider (via LicenseExpirationTask)

## Version 0.3.3

Released on October 17th, 2015.

* oxAuth is upgraded to v2.3.4.
* oxTrust is upgraded to v2.3.4.
* All nodes entrypoints are managed by supervisord.
* Cluster data are distributed to all consumer providers after addition/update/deletion events.
* Recovery command is removed in favor of [gluu-agent](https://github.com/GluuFederation/gluu-agent) recover command.
* License is changed.
* Fixed prometheus config template.
* Fixed templates in oxTrust.

## Version 0.3.2

Released on September 4th, 2015.

* Fixed CN value in OpenDJ self-signed certificate.
* Decreased tokens lifetime in `oxauth-config.xml`.

## Version 0.3.1

Released on August 29th, 2015.

* Fixed path and permission to deployment log files.
* Fixed duplicated node's name (ref: https://github.com/GluuFederation/gluu-flask/issues/32).
* Added `exec-delay` option in recovery command.
* Added validation rule for cluster name.
* oxAuth is upgraded to v2.3.3.
* oxTrust is upgraded to v2.3.3.
* Secured oxTrust by making it running in localhost only. Previously oxTrust is reachable from public network.
* Templates are updated to conform to changes in Community Edition.
* Added `force` optional parameter in Node API to delete specific node regardless of its state.
* Disabled nodes are recovered through recovery command, but excluded from weave network.

## Version 0.3.0

Released on August 4th, 2015.

* License Key and License API is merged into single API, License Key API
* License key is restricted to a single key.
* Registering consumer provider doesn't need `license_id` parameter anymore.
* Added recovery script; available as `gluuapi recover` command.
* oxAuth is upgraded to v2.3.2.
* oxTrust is upgraded to v2.3.2.
* `.ldif` files are updated.
* weave is launched and exposed after registering/updating provider.
* Swagger UI is updated to conform to changes in API.
* Node deletion is disallowed if node's state is set to `IN_PROGRESS` (https://github.com/GluuFederation/gluu-flask/issues/31).
* Fixed duplicated weave IP allocation.
* Fixed issue where certification password use value less than 6 characters.
* Fixed connection to TLS-protected docker daemon.
* Fixed LDAP discovery in oxAuth node (reference: https://github.com/GluuFederation/oxAuth/issues/52).
* Fixed file permission to deploy log files.

## Version 0.2.0

Released on July 12th, 2015.

* Added License Key API.
* Added License API.
* Change the endpoint for Node API from `/node` to `/nodes`.
* Change the endpoint for Cluster API from `/cluster` to `/clusters`.
* Change the endpoint for Provider API from `/provider` to `/providers`.
* Added `ssl_key`, `ssl_cert`, and `ca_cert` parameters in Provider API to support TLS.
* Enable encryption in Weave.
* Docker daemon is protected by TLS.
* Added support for Docker 1.7.
* Added license expiration monitoring.
* Weave is launched and exposed after registering provider.
* Added node state to track the progress of deployment.

## Version 0.1.0

Released on June 12th, 2015.

* Added Provider API to manage providers/servers.
* Two types of providers have been introduced: `master` and `consumer`. Note: `consumer` type is partially supported.
* Added Cluster API to manage Gluu Cluster.
* Added Node API to manage nodes.
* Added `ldap` node (a `gluuopendj` image running OpenDJ v2.6.0).
* Added `oxauth` node (a `gluuoxauth` image running oxAuth v2.2.0).
* Added `oxtrust` node (a `gluuoxtrust` image running oxTrust v2.2.0).
* Added `httpd` node (a `gluuhttpd` image running Apache2 HTTP v2.4.7).
* Added `salt-master` and `salt-minion` for remote execution in nodes.
* Multi-host `docker` networking is handled by [weave](http://weave.works/).
* Nodes monitoring is handled by [prometheus](http://prometheus.io/).
