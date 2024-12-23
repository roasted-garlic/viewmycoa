
import os
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_app():
    """Initialize the application"""
    try:
        # Create static and uploads directories if they don't exist
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        uploads_dir = os.path.join(static_dir, 'uploads')
        
        for directory in [static_dir, uploads_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory at {directory}")

        logger.info("Application initialized successfully")

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
