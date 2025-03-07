
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
    """Find and kill process using the specified port with Replit-compatible approach"""
    try:
        # In Replit, 'lsof' is often not available, so we'll use a more compatible approach
        # First try to find Python processes
        logger.info(f"Looking for processes using port {port}...")
        
        try:
            # Try to use ps to find Python processes
            ps_result = subprocess.run(
                "ps aux | grep python", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            # Look for processes running main.py or app.py
            python_processes = []
            for line in ps_result.stdout.splitlines():
                # Skip the grep process itself
                if "grep python" in line:
                    continue
                    
                # Look for our application processes
                if "main.py" in line or "app.py" in line:
                    # Extract PID (second column in ps output)
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        python_processes.append(pid)
                        logger.info(f"Found Python process: {pid} - {line}")
            
            # Kill found Python processes
            for pid in python_processes:
                try:
                    # Use SIGTERM first for graceful shutdown
                    subprocess.run(f"kill {pid}", shell=True, check=False)
                    logger.info(f"Sent SIGTERM to process {pid}")
                    
                    # Wait briefly then forcefully kill if still running
                    time.sleep(1)
                    
                    # Check if process is still running
                    if subprocess.run(f"ps -p {pid}", shell=True, capture_output=True).returncode == 0:
                        logger.info(f"Process {pid} still running, sending SIGKILL")
                        subprocess.run(f"kill -9 {pid}", shell=True, check=False)
                except Exception as kill_error:
                    logger.warning(f"Error killing process {pid}: {str(kill_error)}")
            
            return True
        except Exception as ps_error:
            logger.warning(f"Error using ps: {str(ps_error)}")
        
        # Fallback to netstat if available
        try:
            netstat_result = subprocess.run(
                f"netstat -tulpn 2>/dev/null | grep :{port}", 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            if netstat_result.stdout:
                for line in netstat_result.stdout.splitlines():
                    # Extract PID/Program name (last column)
                    parts = line.strip().split()
                    if len(parts) >= 7:
                        pid_program = parts[6]
                        # Format is typically "PID/program_name"
                        if "/" in pid_program:
                            pid = pid_program.split("/")[0]
                            logger.info(f"Found process using port {port}: {pid}")
                            try:
                                subprocess.run(f"kill -9 {pid}", shell=True, check=False)
                                logger.info(f"Killed process {pid}")
                            except Exception as kill_error:
                                logger.warning(f"Error killing process {pid}: {str(kill_error)}")
                return True
        except Exception as netstat_error:
            logger.warning(f"Error using netstat: {str(netstat_error)}")
        
        # If we get here, we couldn't identify processes by name or port
        # Just log it and return true so restart can proceed
        logger.info(f"Could not reliably identify processes using port {port}")
        return True
            
    except Exception as e:
        logger.error(f"Error finding/killing process: {str(e)}")
        # Return true anyway so restart can try to proceed
        return True

def restart_application():
    """Restart the Flask application"""
    try:
        # Get port from environment variable or use consistent port for both development and deployment
        # Use port 5000 for consistency across the application
        port = int(os.getenv("PORT", 5000))
        
        # Kill any process using the port
        find_and_kill_process_on_port(port)
        
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
        logger.info(f"Running main.py on port {port}...")
        env = os.environ.copy()
        # Ensure PORT environment variable is set
        env["PORT"] = str(port)
        subprocess.Popen(["python", "main.py"], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env)
        
        # Let the user know the application is restarting
        print("\n" + "="*50)
        print(f"✅ Application restarting on port {port}!")
        print("The server should be available in a few seconds.")
        print("="*50 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Failed to restart application: {str(e)}")
        return False

if __name__ == "__main__":
    restart_application()
