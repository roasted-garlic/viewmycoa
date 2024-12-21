
"""Add square_image_id to Product

Revision ID: add_square_image_id
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('product', sa.Column('square_image_id', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('product', 'square_image_id')
"""Add square_image_id to Product

Revision ID: add_square_image_id
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('product', sa.Column('square_image_id', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('product', 'square_image_id')
