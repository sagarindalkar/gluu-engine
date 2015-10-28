Changelog
=========

Here you can see the full list of changes between each gluu-flask release.

Version 0.4.0
-------------

(release date to be announced)

* Added new `gluushib` docker image based on oxIDP v2.3.4.
* Added new `saml` node (docker container for gluushib).
* Added background task (`gluuapi.task.fswatcher.SAMLWatcherTask`) to monitor and distribute schema and metadata for `saml` node.
* License expiration task is now monitoring `saml` node as well.
* Recovery priority for httpd node is changed to 4. Previous recovery priority value is now taken by `saml` node.
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

Version 0.3.3
-------------

Released on October 17th, 2015.

* oxAuth is upgraded to v2.3.4.
* oxTrust is upgraded to v2.3.4.
* All nodes entrypoints are managed by supervisord.
* Cluster data are distributed to all consumer providers after addition/update/deletion events.
* Recovery command is removed in favor of [gluu-agent](https://github.com/GluuFederation/gluu-agent) recover command.
* License is changed.
* Fixed prometheus config template.
* Fixed templates in oxTrust.

Version 0.3.2
-------------

Released on September 4th, 2015.

* Fixed CN value in OpenDJ self-signed certificate.
* Decreased tokens lifetime in `oxauth-config.xml`.

Version 0.3.1
-------------

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

Version 0.3.0
-------------

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

Version 0.2.0
-------------

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

Version 0.1.0
-------------

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
