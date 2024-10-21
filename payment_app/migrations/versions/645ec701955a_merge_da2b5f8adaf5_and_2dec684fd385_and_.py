"""merge da2b5f8adaf5 and 2dec684fd385 and 988c1e58bc05

Revision ID: 645ec701955a
Revises: 988c1e58bc05, 2dec684fd385, da2b5f8adaf5
Create Date: 2023-01-02 12:31:03.113342

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '645ec701955a'
down_revision = ('988c1e58bc05', '2dec684fd385', 'da2b5f8adaf5')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
