"""Initialize database schema

Revision ID: init_schema
Revises: 
Create Date: 2024-12-20 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'init_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create admin_user table
    op.create_table(
        'admin_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    
    # Create default admin user with proper password hashing
    connection = op.get_bind()
    connection.execute(
        """
        INSERT INTO admin_user (username, password_hash, created_at)
        VALUES (:username, :password_hash, :created_at)
        """,
        {
            'username': 'admin',
            'password_hash': generate_password_hash('admin'),
            'created_at': datetime.utcnow()
        }
    )

def downgrade():
    op.drop_table('admin_user')
