from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    op.create_table('batch_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(8), nullable=False),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('coa_pdf', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_batch_history_batch_number', 'batch_history', ['batch_number'])

def downgrade():
    op.drop_index('ix_batch_history_batch_number', 'batch_history')
    op.drop_table('batch_history')
