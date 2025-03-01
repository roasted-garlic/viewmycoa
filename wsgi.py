
import os
import logging
from app import app

# Import routes after app is created to avoid circular imports
with app.app_context():
    from routes import admin_routes, auth_routes

if __name__ == "__main__":
    # Configure host and port
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    
    # Set up production logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting production server on {host}:{port}")
    
    # Run the app
    app.run(host=host, port=port)
