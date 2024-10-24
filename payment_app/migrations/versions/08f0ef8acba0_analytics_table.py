"""analytics table

Revision ID: 08f0ef8acba0
Revises: 38af1decc2dd
Create Date: 2022-12-22 07:10:24.072520

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '08f0ef8acba0'
down_revision = '38af1decc2dd'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment_analytics',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('transaction_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('order_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('payment_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('payment_method', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('razorpay_status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=True),
    sa.Column('card_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('card_name', sqlmodel.sql.sqltypes.AutoString(length=30), nullable=True),
    sa.Column('card_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('card_network', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('issuer', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
    sa.Column('step', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
    sa.Column('reason', mysql.LONGTEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payment_analytics')
    # ### end Alembic commands ###
