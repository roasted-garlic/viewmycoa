"""add label fields

Revision ID: add_label_fields
Create Date: 2024-12-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_label_fields'
down_revision = 'add_sku_field'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('product', sa.Column('mg_per_piece', sa.String(50)))
    op.add_column('product', sa.Column('count', sa.String(50)))
    op.add_column('product', sa.Column('per_piece_g', sa.String(50)))
    op.add_column('product', sa.Column('net_weight_g', sa.String(50)))
    op.add_column('product', sa.Column('cannabinoid', sa.String(100)))
    op.add_column('product', sa.Column('qr_code', sa.String(255)))
    op.add_column('product', sa.Column('expire_date', sa.String(50)))
    op.add_column('product', sa.Column('disclaimer', sa.Text))
    op.add_column('product', sa.Column('manufactured_by', sa.String(255)))

def downgrade():
    op.drop_column('product', 'mg_per_piece')
    op.drop_column('product', 'count')
    op.drop_column('product', 'per_piece_g')
    op.drop_column('product', 'net_weight_g')
    op.drop_column('product', 'cannabinoid')
    op.drop_column('product', 'qr_code')
    op.drop_column('product', 'expire_date')
    op.drop_column('product', 'disclaimer')
    op.drop_column('product', 'manufactured_by')
