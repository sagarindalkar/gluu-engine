"""create tables

Revision ID: cc03834f1d24
Revises:
Create Date: 2017-03-24 22:07:25.269989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc03834f1d24'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_table(
            'clusters',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('name', sa.Unicode(length=255), nullable=True),
            sa.Column('description', sa.Unicode(length=255), nullable=True),
            sa.Column('ox_cluster_hostname', sa.Unicode(length=255), nullable=True),
            sa.Column('org_name', sa.Unicode(length=128), nullable=True),
            sa.Column('country_code', sa.Unicode(length=2), nullable=True),
            sa.Column('city', sa.Unicode(length=64), nullable=True),
            sa.Column('state', sa.Unicode(length=64), nullable=True),
            sa.Column('admin_email', sa.Unicode(length=255), nullable=True),
            sa.Column('passkey', sa.Unicode(length=255), nullable=True),
            sa.Column('admin_pw', sa.Unicode(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'container_logs',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('container_name', sa.Unicode(length=255), nullable=True),
            sa.Column('state', sa.Unicode(length=32), nullable=True),
            sa.Column('setup_log', sa.Unicode(length=255), nullable=True),
            sa.Column('teardown_log', sa.Unicode(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'containers',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('cluster_id', sa.Unicode(length=36), nullable=True),
            sa.Column('node_id', sa.Unicode(length=36), nullable=True),
            sa.Column('container_attrs', sa.JSON(), nullable=True),
            sa.Column('name', sa.Unicode(length=255), nullable=True),
            sa.Column('state', sa.Unicode(length=32), nullable=True),
            sa.Column('type', sa.Unicode(length=32), nullable=True),
            sa.Column('hostname', sa.Unicode(length=255), nullable=True),
            sa.Column('cid', sa.Unicode(length=128), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'ldap_settings',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('host', sa.Unicode(length=255), nullable=True),
            sa.Column('port', sa.Integer(), nullable=True),
            sa.Column('bind_dn', sa.Unicode(length=255), nullable=True),
            sa.Column('encoded_bind_password', sa.Unicode(length=255), nullable=True),
            sa.Column('encoded_salt', sa.Unicode(length=255), nullable=True),
            sa.Column('inum_appliance', sa.Unicode(length=255), nullable=True),
            sa.Column('inum_org', sa.Unicode(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'license_keys',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('name', sa.Unicode(length=255), nullable=True),
            sa.Column('code', sa.Unicode(length=255), nullable=True),
            sa.Column('public_key', sa.Text(), nullable=True),
            sa.Column('public_password', sa.Unicode(length=255), nullable=True),
            sa.Column('license_password', sa.Unicode(length=255), nullable=True),
            sa.Column('signed_license', sa.Text(), nullable=True),
            sa.Column('valid', sa.Boolean(), nullable=True),
            sa.Column('populated_at', sa.BigInteger(), nullable=True),
            sa.Column('passkey', sa.Unicode(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'nodes',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('name', sa.Unicode(length=36), nullable=True),
            sa.Column('provider_id', sa.Unicode(length=36), nullable=True),
            sa.Column('type', sa.Unicode(length=32), nullable=True),
            sa.Column('state_attrs', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass

    try:
        op.create_table(
            'providers',
            sa.Column('id', sa.Unicode(length=36), nullable=False),
            sa.Column('name', sa.Unicode(length=255), nullable=True),
            sa.Column('driver', sa.Unicode(length=128), nullable=True),
            sa.Column('driver_attrs', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except sa.exc.InternalError as exc:
        errno, _ = exc.orig
        if errno == 1050:
            pass


def downgrade():
    # op.drop_table('providers')
    # op.drop_table('nodes')
    # op.drop_table('license_keys')
    # op.drop_table('ldap_settings')
    # op.drop_table('containers')
    # op.drop_table('container_logs')
    # op.drop_table('clusters')
    pass
