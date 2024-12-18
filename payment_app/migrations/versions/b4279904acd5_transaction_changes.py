"""transaction changes

Revision ID: b4279904acd5
Revises: 7656daf4221e
Create Date: 2022-08-09 18:39:59.962578

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b4279904acd5'
down_revision = '7656daf4221e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "transactions",
        "payment_id",
        new_column_name="gateway_payment_id",
        existing_type=mysql.VARCHAR(length=100),
        nullable=True,
    )
    op.drop_index('ix_transactions_payment_id', table_name='transactions')
    op.create_index(op.f('ix_transactions_gateway_payment_id'), 'transactions', ['gateway_payment_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "transactions",
        "gateway_payment_id",
        new_column_name="payment_id",
        existing_type=mysql.VARCHAR(length=100),
        nullable=True,
    )
    op.drop_index(op.f('ix_transactions_gateway_payment_id'), table_name='transactions')
    op.create_index('ix_transactions_payment_id', 'transactions', ['payment_id'], unique=False)
    # ### end Alembic commands ###
