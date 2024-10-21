"""empty message

Revision ID: 38af1decc2dd
Revises: 7cecd4e6cb37, da2b5f8adaf5
Create Date: 2022-12-22 07:09:42.551106

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '38af1decc2dd'
down_revision = ('7cecd4e6cb37', 'da2b5f8adaf5')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
