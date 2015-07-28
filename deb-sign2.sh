#!/usr/bin/expect -f
exp_internal 0
spawn dpkg-sig -s builder -k 0544BA38 $argv
expect "Enter passphrase: " { send "hsdif923md@5\r" }
expect eof
