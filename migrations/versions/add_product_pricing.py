"""Add product cost and price fields

Revision ID: add_product_pricing
Revises: init_admin_schema
Create Date: 2024-12-20 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_product_pricing'
down_revision = 'init_admin_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Add cost and price columns to product table
    op.add_column('product',
        sa.Column('cost', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column('product',
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True)
    )

def downgrade():
    op.drop_column('product', 'price')
    op.drop_column('product', 'cost')
