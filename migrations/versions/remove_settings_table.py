
"""remove settings table

Revision ID: remove_settings_table
Create Date: 2024-12-21 04:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'remove_settings_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.drop_table('settings')

def downgrade():
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('show_square_id_controls', sa.Boolean(), nullable=True),
        sa.Column('show_square_image_id_controls', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
