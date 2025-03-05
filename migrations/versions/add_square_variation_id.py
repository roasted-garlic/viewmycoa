"""add square variation id column

Revision ID: add_square_variation_id
Revises: 
Create Date: 2025-03-05 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_square_variation_id'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add the square_variation_id column to the product table
    op.add_column('product', sa.Column('square_variation_id', sa.String(255), nullable=True))


def downgrade():
    # Remove the square_variation_id column from the product table
    op.drop_column('product', 'square_variation_id')