
import os
import logging
import signal
import subprocess
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import routes after app is created to avoid circular imports
with app.app_context():
    from routes import admin_routes, auth_routes

def find_free_port(start_port=8080, max_port=9000):
    """Find a free port starting from start_port"""
    import socket
    
    port = start_port
    while port < max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                logger.info(f"Found free port: {port}")
                return port
            except OSError:
                logger.info(f"Port {port} is in use, trying next port")
                port += 1
    
    # If no ports are available, return a different port range
    logger.warning("No free ports found in specified range, using port 8000")
    return 8000

if __name__ == "__main__":
    # Configure host and find a free port
    host = "0.0.0.0"
    port = find_free_port()
    
    logger.info(f"Starting application on {host}:{port}")
    app.run(host=host, port=port, debug=True)
