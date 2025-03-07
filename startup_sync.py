
#!/usr/bin/env python3
import os
import logging
import subprocess
import sys
import time
import argparse
import signal
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StartupSync")

# Global variables
LOCK_FILE = "sync_in_progress.lock"
MAX_LOCK_AGE = 600  # 10 minutes in seconds
TIMEOUT = 300  # Default timeout in seconds

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run startup sync operations')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--force', action='store_true', help='Force sync even if lock file exists')
parser.add_argument('--timeout', type=int, default=TIMEOUT, help=f'Max execution time in seconds (default: {TIMEOUT})')
args = parser.parse_args()

# Configure logging based on arguments
if args.debug:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

# Set timeout based on arguments
TIMEOUT = args.timeout

# Function to clean up the lock file
def cleanup_lock_file():
    """Clean up lock file at exit"""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
            logger.info("Removed sync lock file at exit")
        except Exception as e:
            logger.error(f"Failed to remove lock file at exit: {str(e)}")

# Register cleanup function to run at exit
atexit.register(cleanup_lock_file)

# Handle timeout
def timeout_handler(signum, frame):
    """Handle timeout signal"""
    logger.error(f"Sync operation timed out after {TIMEOUT} seconds")
    # Cleanup will be done by atexit handler
    sys.exit(1)

# Set timeout handler
signal.signal(signal.SIGALRM, timeout_handler)

def acquire_lock():
    """Try to acquire the lock file"""
    # Check if we're in production
    if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
        logger.info("Skipping startup sync in production environment")
        return False
        
    # Check if lock file exists
    if os.path.exists(LOCK_FILE):
        # If force flag is set, remove the lock and continue
        if args.force:
            logger.warning("Force flag set, removing existing lock file")
            try:
                os.remove(LOCK_FILE)
            except Exception as e:
                logger.error(f"Failed to remove lock file: {str(e)}")
                return False
        else:
            # Check if the lock is stale
            try:
                lock_stat = os.stat(LOCK_FILE)
                lock_age = time.time() - lock_stat.st_mtime
                
                if lock_age > MAX_LOCK_AGE:
                    logger.warning(f"Found stale lock file (age: {lock_age:.1f}s), removing it")
                    try:
                        os.remove(LOCK_FILE)
                    except Exception as e:
                        logger.error(f"Failed to remove stale lock file: {str(e)}")
                        return False
                else:
                    logger.info(f"Sync already in progress (lock age: {lock_age:.1f}s), skipping")
                    return False
            except Exception as e:
                logger.error(f"Error checking lock file: {str(e)}")
                return False
    
    # Create lock file
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(f"Sync started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logger.error(f"Failed to create lock file: {str(e)}")
        return False

def run_startup_sync():
    """Run both image and PDF sync operations when the development environment starts"""
    # Activate timeout alarm
    signal.alarm(TIMEOUT)
    
    try:
        if not acquire_lock():
            return
            
        logger.info("Starting sync operations on development environment startup")
        
        # Small delay to ensure database and Flask app are initialized
        time.sleep(3)
        
        # Run image sync
        logger.info("Running image sync (download new, remove deleted)...")
        img_result = subprocess.run(
            [sys.executable, "sync_images.py"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT//2  # Set subprocess timeout to half the total timeout
        )
        if img_result.returncode == 0:
            logger.info("Image sync completed successfully")
            # Log details from image sync output
            for line in img_result.stdout.splitlines():
                if "Downloaded" in line or "orphaned" in line:
                    logger.info(f"  {line.strip()}")
        else:
            logger.error(f"Image sync failed: {img_result.stderr}")
            
        # Small delay between operations
        time.sleep(2)
        
        # Run PDF sync
        logger.info("Running PDF sync (download new, remove deleted)...")
        pdf_result = subprocess.run(
            [sys.executable, "sync_pdfs.py"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT//2  # Set subprocess timeout to half the total timeout
        )
        if pdf_result.returncode == 0:
            logger.info("PDF sync completed successfully")
            # Log details from PDF sync output
            for line in pdf_result.stdout.splitlines():
                if "Downloaded" in line or "orphaned" in line:
                    logger.info(f"  {line.strip()}")
        else:
            logger.error(f"PDF sync failed: {pdf_result.stderr}")
            
        logger.info("Startup sync operations completed")
        
    except subprocess.TimeoutExpired:
        logger.error("A sync subprocess timed out")
    except Exception as e:
        logger.error(f"Error during startup sync: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
    finally:
        # Cancel the alarm
        signal.alarm(0)
        # Lock file cleanup is handled by atexit

if __name__ == "__main__":
    run_startup_sync()
