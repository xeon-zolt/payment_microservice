"""make t_id nullable

Revision ID: da2b5f8adaf5
Revises: 6b28e9b4490b
Create Date: 2022-12-13 07:14:52.365516

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'da2b5f8adaf5'
down_revision = '6b28e9b4490b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('transaction_callbacks', 'transaction_id',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('transaction_callbacks', 'transaction_id',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    # ### end Alembic commands ###
