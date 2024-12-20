
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('product', sa.Column('cost', sa.Float(), nullable=True))
    op.add_column('product', sa.Column('price', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('product', 'cost')
    op.drop_column('product', 'price')
