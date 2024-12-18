
import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_app():
    """Initialize the application"""
    try:
        # Create static directories
        dirs = ['static', 'static/uploads', 'static/pdfs']
        for directory in dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")

        # Initialize database
        with app.app_context():
            import models
            db.create_all()
            logger.info("Database initialized")

    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        init_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start: {str(e)}")
