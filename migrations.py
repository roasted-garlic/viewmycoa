from flask_migrate import Migrate
from app import app, db

migrate = Migrate(app, db)

def create_migration():
    """Create a new migration for adding the sku column"""
    with app.app_context():
        migrate.init_app(app, db)
        from alembic import op
        import sqlalchemy as sa
        op.add_column('product', sa.Column('sku', sa.String(8), nullable=True, unique=True))

if __name__ == '__main__':
    from flask.cli import FlaskGroup
    cli = FlaskGroup(app)
    create_migration()
