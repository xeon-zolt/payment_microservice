"""refund id set to unique

Revision ID: 669e8866a922
Revises: 61323e84fcb5
Create Date: 2022-04-27 17:05:49.878050

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '669e8866a922'
down_revision = '61323e84fcb5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_refund_transactions_refund_id', table_name='refund_transactions')
    op.create_unique_constraint(None, 'refund_transactions', ['refund_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'refund_transactions', type_='unique')
    op.create_index('ix_refund_transactions_refund_id', 'refund_transactions', ['refund_id'], unique=False)
    # ### end Alembic commands ###
