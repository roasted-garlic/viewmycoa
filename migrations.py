from flask_migrate import Migrate
from app import app, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

migrate = Migrate(app, db)

def init_migrations():
    """Initialize migrations"""
    try:
        migrate.init_app(app, db)
        logger.info("Migrations initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing migrations: {e}")
        raise

if __name__ == '__main__':
    init_migrations()
