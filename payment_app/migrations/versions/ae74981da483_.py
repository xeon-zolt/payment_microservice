"""empty message

Revision ID: ae74981da483
Revises: 91530800da4d, d9011ec1ec18
Create Date: 2022-07-11 18:40:30.176811

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'ae74981da483'
down_revision = ('91530800da4d', 'd9011ec1ec18')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
