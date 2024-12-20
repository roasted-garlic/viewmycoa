"""Add product cost and price columns

Revision ID: add_product_cost_price
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add cost and price columns to product table
    op.add_column('product', sa.Column('cost', sa.Float(), nullable=True))
    op.add_column('product', sa.Column('price', sa.Float(), nullable=True))

def downgrade():
    # Remove cost and price columns from product table
    op.drop_column('product', 'cost')
    op.drop_column('product', 'price')
