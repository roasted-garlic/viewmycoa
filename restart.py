
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
            
            # Wait for the port to be released
            time.sleep(2)
            return True
        else:
            logger.info(f"No process found using port {port}")
            return False
    except Exception as e:
        logger.error(f"Error finding/killing process: {str(e)}")
        return False

def start_application():
    try:
        # Make sure port 5000 is free
        find_and_kill_process_on_port(5000)
        
        # Set environment variable
        os.environ["FLASK_APP"] = "app.py"
        
        # Upgrade the database
        result = subprocess.run(["flask", "db", "upgrade"], check=True)
        
        # Start the application
        process = subprocess.Popen(["python", "main.py"])
        logger.info(f"Application started with PID: {process.pid}")
        
        # Give some time for the app to start
        time.sleep(3)
        
        # Check if the application is running
        if process.poll() is None:
            logger.info("Application is running successfully")
            return True
        else:
            logger.error(f"Application failed to start. Exit code: {process.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Command execution failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        return False

if __name__ == "__main__":
    # First kill any existing processes
    find_and_kill_process_on_port(5000)
    
    # Then start the application
    if start_application():
        print("\n" + "="*50)
        print("✅ Application started successfully!")
        print("Open your browser and navigate to the Replit URL")
        print("="*50 + "\n")
    else:
        print("\n" + "="*50)
        print("❌ Failed to start application")
        print("="*50 + "\n")
