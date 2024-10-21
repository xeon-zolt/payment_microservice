"""empty message

Revision ID: c74d1082331d
Revises: 09dd15f01e87, 18e4bfcef955
Create Date: 2022-11-10 08:12:00.429223

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'c74d1082331d'
down_revision = ('09dd15f01e87', '18e4bfcef955')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
