#!/bin/bash
repo_path="/var/www/html/ubuntu"
trusty="/var/www/html/ubuntu/pool/main/trusty"
trustydevel="/var/www/html/ubuntu/pool/main/trusty-devel"
gpg_pass="/home/tomcat/.gnupg/.pass"
build=$1
if [ -n $build ]; then
    build="unstable"
fi
if [ "$(ls -f *.deb)" ]; then
    debfile=`ls -f *.deb`
    #/usr/bin/dpkg-sig -k 0544BA38 -f $gpg_pass -s builder $debfile
    ./deb-sign2.sh $debfile
    version="trusty"
    if [ "$build" == "trusty" ]; then
        /bin/cp -f $debfile $trusty
        cd $repo_path
        `sh updaterepo-trusty.sh`
    else
        /bin/cp -f $debfile $trustydevel
        cd $repo_path
        `sh updaterepo-trusty-devel.sh`
        version="trusty-devel"
    fi
    echo  "Download deb at http://repo.gluu.org/ubuntu/pool/main/$version/$debfile"
else
     exit 1
fi
