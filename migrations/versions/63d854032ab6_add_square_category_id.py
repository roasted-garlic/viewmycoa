"""Add square category id

Revision ID: 63d854032ab6
Revises: 
Create Date: 2024-12-21 05:24:54.317589

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63d854032ab6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_user')
    with op.batch_alter_table('batch_history', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'product', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.add_column(sa.Column('square_category_id', sa.String(length=255), nullable=True))

    with op.batch_alter_table('generated_pdf', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'product', ['product_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('product_categories', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'product', ['product_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product_categories', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('generated_pdf', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('category', schema=None) as batch_op:
        batch_op.drop_column('square_category_id')

    with op.batch_alter_table('batch_history', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    op.create_table('admin_user',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='admin_user_pkey'),
    sa.UniqueConstraint('username', name='admin_user_username_key')
    )
    # ### end Alembic commands ###
