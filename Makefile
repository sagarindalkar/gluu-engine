run:
	@gluuengine runserver

test:
	@tox

develop:
	@python setup.py develop

install:
	@python setup.py install
