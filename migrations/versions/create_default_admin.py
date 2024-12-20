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
    from datetime import datetime
    connection = op.get_bind()
    connection.execute(
        """
        INSERT INTO admin_user (username, password_hash, created_at)
        VALUES ('admin', :password_hash, :created_at)
        ON CONFLICT (username) DO NOTHING
        """,
        {
            'password_hash': generate_password_hash('admin', method='sha256'),
            'created_at': datetime.utcnow()
        }
    )

def downgrade():
    op.execute("DELETE FROM admin_user WHERE username = 'admin'")
