from flask_migrate import Migrate
from app import app, db
import os

migrate = Migrate(app, db)

def init_migrations():
    """Initialize migrations directory"""
    with app.app_context():
        if not os.path.exists('migrations'):
            from flask_migrate import init, migrate, upgrade
            init()
            migrate()
            upgrade()

def create_coa_migration():
    """Create a new migration for adding the coa_pdf column"""
    with app.app_context():
        migrate.init_app(app, db)
        from alembic import op
        import sqlalchemy as sa
        op.add_column('product', sa.Column('coa_pdf', sa.String(500), nullable=True))

if __name__ == '__main__':
    from flask.cli import FlaskGroup
    cli = FlaskGroup(app)
    init_migrations()
    create_coa_migration()
