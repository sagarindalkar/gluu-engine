IP=`hostname -I | cut -d ' ' -f 1`
run:
	@SALT_MASTER_IPADDR=${IP} gluuapi

test:
	@tox

develop:
	@python setup.py develop

install:
	@python setup.py install
