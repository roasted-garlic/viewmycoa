"""initial migration

Revision ID: initial
Create Date: 2024-12-12 21:19:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create Template table first (referenced by Product table)
    template_table = op.create_table('template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Product table with template_id reference
    product_table = op.create_table('product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('batch_number', sa.String(length=8), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('product_image', sa.String(length=500), nullable=True),
        sa.Column('label_image', sa.String(length=500), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Generated PDF table with product reference
    op.create_table('generated_pdf',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('generated_pdf')
    op.drop_table('product')
    op.drop_table('template')
