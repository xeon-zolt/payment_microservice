"""update_column_invoice_id_to_plink_id

Revision ID: 988c1e58bc05
Revises: 17f81b2050e9
Create Date: 2022-12-07 18:04:16.786828

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '988c1e58bc05'
down_revision = '17f81b2050e9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("payment_links",column_name="invoice_id", new_column_name="plink_id", existing_type=mysql.VARCHAR(length=64), nullable=False)    
    op.drop_constraint(constraint_name="payment_links_ibfk_1", table_name="payment_links", type_="foreignkey")
    op.drop_index('payment_link_comp_index', table_name='payment_links')
    op.create_foreign_key(constraint_name="payment_links_ibfk_1", referent_table="transactions", local_cols=["transaction_id"], remote_cols=["id"], source_table="payment_links")
    op.create_index('payment_link_comp_index', 'payment_links', ['transaction_id', 'plink_id'], unique=False)
    # op.create_con
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transactions', 'store_type')
    op.add_column('payment_links', sa.Column('invoice_id', mysql.VARCHAR(length=64), nullable=False))
    op.drop_index('payment_link_comp_index', table_name='payment_links')
    op.create_index('payment_link_comp_index', 'payment_links', ['transaction_id', 'invoice_id'], unique=False)
    op.drop_column('payment_links', 'plink_id')
    # ### end Alembic commands ###
