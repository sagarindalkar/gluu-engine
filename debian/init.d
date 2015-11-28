#!/bin/sh
### BEGIN INIT INFO
# Provides:          gluuapi
# Required-Start:    $local_fs $network $remote_fs $syslog
# Required-Stop:     $local_fs $network $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: <Enter a short description of the software>
# Description:       <Enter a long description of the software>
#                    <...>
#                    <...>
### END INIT INFO

# Author: Adrian Alves <adrian@gluu.org>

# Do NOT "set -e"

# PATH should only include /usr/ * if it runs after the mountnfs.sh script
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="gluuapi"
NAME=gluuapi
DAEMON=/usr/bin/gluuapi
DAEMON_ARGS=""
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME
API_ENV=
SALT_MASTER_IPADDR=
HOST=
PORT=

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$NAME ] && . /etc/default/$NAME

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.2-14) to ensure that this file is present
# and status_of_proc is working.
. /lib/lsb/init-functions

case "$1" in
  start)
	API_ENV=$API_ENV SALT_MASTER_IPADDR=$SALT_MASTER_IPADDR HOST=$HOST PORT=$PORT $DAEMON daemon start
	;;
  stop)
	API_ENV=$API_ENV SALT_MASTER_IPADDR=$SALT_MASTER_IPADDR HOST=$HOST PORT=$PORT $DAEMON daemon stop
	;;
  status)
	API_ENV=$API_ENV SALT_MASTER_IPADDR=$SALT_MASTER_IPADDR HOST=$HOST PORT=$PORT $DAEMON daemon status
	;;
  restart)
	API_ENV=$API_ENV SALT_MASTER_IPADDR=$SALT_MASTER_IPADDR HOST=$HOST PORT=$PORT $DAEMON daemon restart
	;;
  *)
	API_ENV=$API_ENV SALT_MASTER_IPADDR=$SALT_MASTER_IPADDR HOST=$HOST PORT=$PORT $DAEMON daemon
	;;
esac
