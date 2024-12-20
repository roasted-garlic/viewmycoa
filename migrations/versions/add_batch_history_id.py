
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('generated_pdf', sa.Column('batch_history_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_generated_pdf_batch_history', 'generated_pdf', 'batch_history', ['batch_history_id'], ['id'], ondelete='CASCADE')

def downgrade():
    op.drop_constraint('fk_generated_pdf_batch_history', 'generated_pdf', type_='foreignkey')
    op.drop_column('generated_pdf', 'batch_history_id')
