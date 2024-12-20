"""Add square catalog id

Revision ID: add_square_catalog_id
Revises: 
Create Date: 2024-12-20 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_square_catalog_id_001'  # Make it unique
down_revision = None  # This will be our first migration
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('product', sa.Column('square_catalog_id', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('product', 'square_catalog_id')
