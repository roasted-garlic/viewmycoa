import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_app():
    """Initialize the application"""
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            logger.info(f"Created upload directory at {upload_dir}")

        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            logger.info(f"Created static directory at {static_dir}")

        # Initialize database
        with app.app_context():
            import models  # Import models before creating tables
            db.create_all()
            logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        raise

def main():
    """Main application entry point"""
    try:
        # Initialize the application
        init_app()

        # Configure host and port
        host = "0.0.0.0"  # Listen on all available interfaces
        port = 5000       # Use port 5000 as specified

        logger.info(f"Starting application on {host}:{port}")
        
        # Run the Flask application
        app.run(
            host=host,
            port=port,
            debug=True,  # Enable debug mode
            use_reloader=True  # Enable auto-reload on code changes
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
