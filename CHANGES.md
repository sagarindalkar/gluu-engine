Changelog
=========

Here you can see the full list of changes between each gluu-flask release.

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
