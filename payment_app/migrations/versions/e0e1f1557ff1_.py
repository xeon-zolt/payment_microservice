"""empty message

Revision ID: e0e1f1557ff1
Revises: a39bce17d048, 49eb918c4dd0
Create Date: 2022-09-29 09:48:18.876108

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'e0e1f1557ff1'
down_revision = ('a39bce17d048', '49eb918c4dd0')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
