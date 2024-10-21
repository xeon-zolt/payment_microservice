"""callbacks table

Revision ID: 7656daf4221e
Revises: a15f94f97c9f
Create Date: 2022-07-27 16:13:23.251891

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7656daf4221e'
down_revision = 'a15f94f97c9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transaction_callbacks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('event', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('callback', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
              nullable=True),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('transactions', sa.Column('callback_response', sa.JSON(), nullable=True))
    op.add_column('transactions', sa.Column('payment_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    op.create_index(op.f('ix_transactions_payment_id'), 'transactions', ['payment_id'], unique=False)
    op.drop_column('transactions', 'callable_response')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transactions', sa.Column('callable_response', mysql.JSON(), nullable=True))
    op.drop_index(op.f('ix_transactions_payment_id'), table_name='transactions')
    op.drop_column('transactions', 'payment_id')
    op.drop_column('transactions', 'callback_response')
    op.drop_table('transaction_callbacks')
    # ### end Alembic commands ###