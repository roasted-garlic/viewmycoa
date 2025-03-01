
#!/usr/bin/env python3
import os
import subprocess
import time
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_and_kill_process_on_port(port):
    """Find and kill process using the specified port"""
    try:
        # Find process using the port
        result = subprocess.run(
            f"lsof -i :{port} -t", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.stdout:
            pid = result.stdout.strip()
            logger.info(f"Found process {pid} using port {port}")
            
            # Kill the process
            subprocess.run(f"kill -9 {pid}", shell=True)
            logger.info(f"Killed process {pid}")
            return True
        else:
            logger.info(f"No process found using port {port}")
            return False
    except Exception as e:
        logger.error(f"Error finding/killing process: {str(e)}")
        return False

def restart_application():
    """Restart the Flask application"""
    try:
        # Kill any process using port 5000
        find_and_kill_process_on_port(5000)
        
        # Wait a moment for the port to be released
        time.sleep(1)
        
        # Start the application
        logger.info("Starting application...")
        os.environ["FLASK_APP"] = "app.py"
        subprocess.run(["flask", "db", "upgrade"], check=True)
        
        # Run the main script
        logger.info("Running main.py...")
        exec(open("main.py").read())
        
        return True
    except Exception as e:
        logger.error(f"Failed to restart application: {str(e)}")
        return False

if __name__ == "__main__":
    restart_application()
