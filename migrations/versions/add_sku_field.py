"""add sku field

Revision ID: add_sku_field
Create Date: 2024-12-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_sku_field'
down_revision = 'rename_title_to_name'
branch_labels = None
depends_on = None

def upgrade():
    # Add SKU column with same format as batch_number (8 chars)
    op.add_column('product', sa.Column('sku', sa.String(8), unique=True))

def downgrade():
    op.drop_column('product', 'sku')
