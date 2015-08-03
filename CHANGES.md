Changelog
=========

Here you can see the full list of changes between each gluu-flask release.

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
