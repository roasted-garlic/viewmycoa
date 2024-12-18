
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('product', sa.Column('coa_pdf', sa.String(500)))

def downgrade():
    op.drop_column('product', 'coa_pdf')
