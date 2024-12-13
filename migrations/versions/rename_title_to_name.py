"""rename title to name

Revision ID: rename_title_to_name
Create Date: 2024-12-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'rename_title_to_name'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('product', 'title', new_column_name='name')

def downgrade():
    op.alter_column('product', 'name', new_column_name='title')
