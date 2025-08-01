"""update db_promo

Revision ID: 8a1f647c9f96
Revises: 64c7783427f9
Create Date: 2025-07-21 14:30:05.091988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a1f647c9f96'
down_revision = '64c7783427f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('promo_codes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('restaurant_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'restaurants', ['restaurant_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('promo_codes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('restaurant_id')

    # ### end Alembic commands ###
