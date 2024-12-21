"""add product square image id

Revision ID: add_product_square_image
Create Date: 2024-12-21 02:54:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_product_square_image'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('product', sa.Column('square_image_id', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('product', 'square_image_id')
