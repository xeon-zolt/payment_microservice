"""transactions api_status type change

Revision ID: c9b9b7705a63
Revises: b4279904acd5
Create Date: 2022-08-09 18:47:28.314447

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c9b9b7705a63'
down_revision = 'b4279904acd5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('transactions', 'api_status',
               existing_type=mysql.TINYINT(),
               type_=sa.SMALLINT(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('transactions', 'api_status',
               existing_type=sa.SMALLINT(),
               type_=mysql.TINYINT(),
               existing_nullable=True)
    # ### end Alembic commands ###
