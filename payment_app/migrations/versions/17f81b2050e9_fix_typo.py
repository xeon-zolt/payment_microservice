"""fix typo

Revision ID: 17f81b2050e9
Revises: c74d1082331d
Create Date: 2022-11-25 07:34:56.844692

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '17f81b2050e9'
down_revision = 'c74d1082331d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "refund_transactions",
        "callable_response",
        new_column_name="callback_response",
        existing_type=sa.JSON(),
        nullable=True,
    )

    #op.alter_column('refund_transactions', sa.Column('callback_response', sa.JSON(), nullable=True))
    #op.drop_column('refund_transactions', 'callable_response')
    # ### end Alembic commands ###


def downgrade():
    op.alter_column(
        "refund_transactions",
        "callback_response",
        new_column_name="callable_response",
        existing_type=sa.JSON(),
        nullable=True,
    )
    # ### commands auto generated by Alembic - please adjust! ###
    #op.alter_column('refund_transactions', sa.Column('callable_response', mysql.JSON(), nullable=True))
    #op.drop_column('refund_transactions', 'callback_response')
    # ### end Alembic commands ###
