"""add template_id column

Revision ID: add_template_id
Create Date: 2024-12-12 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_template_id'
down_revision = 'initial'
branch_labels = None
depends_on = None

def upgrade():
    # Add template_id column to product table
    op.add_column('product', sa.Column('template_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_product_template_id',
        'product', 'template',
        ['template_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    op.drop_constraint('fk_product_template_id', 'product', type_='foreignkey')
    op.drop_column('product', 'template_id')
