"""
Gluu Engine
-----------

Gluu Server Docker Edition REST API .
"""
import codecs
import os
import re
from setuptools import setup
from setuptools import find_packages


def find_version(*file_paths):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, *file_paths), 'r') as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="gluuengine",
    version=find_version("gluuengine", "__init__.py"),
    url="https://github.com/GluuFederation/gluu-engine",
    license="Gluu",
    author="Gluu",
    author_email="info@gluu.org",
    description="Gluu Server Docker Edition REST API ",
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        "Flask-RESTful",
        "Flask",
        "crochet",
        "docker-py>=1.8.0",
        "m2crypto",
        "marshmallow",
        "flask_marshmallow",
        "blinker",
        "flask-pymongo",
        "gunicorn",
        "futures",
        "click",
        "pymysql",
        "schematics",
        "dataset",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: OSI Approved",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": ["gluuengine=gluuengine.cli:main"],
    },
)
