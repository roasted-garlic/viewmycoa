"""Create default admin user

Revision ID: create_default_admin
Revises: add_admin_user_table
Create Date: 2024-12-20 04:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = 'create_default_admin'
down_revision = 'add_admin_user_table'
branch_labels = None
depends_on = None

def upgrade():
    # Create the default admin user with a secure password hash
    admin_table = sa.table('admin_user',
        sa.column('username', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('created_at', sa.DateTime)
    )
    
    op.bulk_insert(admin_table, [
        {
            'username': 'admin',
            'password_hash': generate_password_hash('admin', method='sha256'),
            'created_at': sa.func.now()
        }
    ])

def downgrade():
    op.execute("DELETE FROM admin_user WHERE username = 'admin'")
