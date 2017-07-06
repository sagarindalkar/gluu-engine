# DB Migration

Run command below whenever table schema has been modified:

    db migrate -m "<short description>"

Afterwards, upgrade the schema using command below:

    db upgrade

__WARNING__: the opposite of `db upgrade` command is `db downgrade`; this command should be taken carefully.
