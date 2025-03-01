
import os
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import routes after app is created to avoid circular imports
with app.app_context():
    from routes import admin_routes, auth_routes

if __name__ == "__main__":
    # Configure host and port
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    
    # Kill any existing process on this port
    import subprocess
    try:
        subprocess.run(f"lsof -i :{port} -t | xargs kill -9", shell=True)
        logger.info(f"Killed existing process on port {port}")
    except Exception as e:
        logger.warning(f"No process to kill on port {port}: {str(e)}")
    
    # Run the Flask application
    logger.info(f"Starting application on {host}:{port}")
    app.run(host=host, port=port, debug=True)
