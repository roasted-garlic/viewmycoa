
from flask_migrate import Migrate
from app import app, db

migrate = Migrate()

def init_migrations():
    migrate.init_app(app, db)

with app.app_context():
    init_migrations()
