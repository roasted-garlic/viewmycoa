
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
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    logger.info(f"Found process {pid} using port {port}")
                    try:
                        # Kill the process
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                        logger.info(f"Killed process {pid}")
                    except subprocess.CalledProcessError:
                        logger.warning(f"Failed to kill process {pid}")
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
        time.sleep(2)
        
        # Start the application
        logger.info("Starting application...")
        os.environ["FLASK_APP"] = "app.py"
        
        # Run flask migration
        try:
            subprocess.run(["flask", "db", "upgrade"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Database migration error: {str(e)}")
            logger.info("Continuing with application startup...")
        
        # Run the main script in background
        logger.info("Running main.py...")
        subprocess.Popen(["python", "main.py"], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        
        # Let the user know the application is restarting
        print("\n" + "="*50)
        print("✅ Application restarting!")
        print("The server should be available in a few seconds.")
        print("="*50 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Failed to restart application: {str(e)}")
        return False

if __name__ == "__main__":
    restart_application()
