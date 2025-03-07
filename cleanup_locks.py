#!/usr/bin/env python3
import os
import logging
import time
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CleanupLocks")

def cleanup_lock_files():
    """Clean up stale lock files"""
    lock_file = "sync_in_progress.lock"
    
    if not os.path.exists(lock_file):
        logger.info("No lock file found, nothing to clean up.")
        return 0
    
    # Check lock file age
    try:
        lock_stat = os.stat(lock_file)
        lock_age = time.time() - lock_stat.st_mtime
        
        logger.info(f"Found lock file (age: {lock_age:.1f} seconds)")
        
        # Check if the process that created the lock is still running
        # For simplicity, we'll just check if any sync-related scripts are running
        import subprocess
        ps_result = subprocess.run(
            ["ps", "-ef"], 
            capture_output=True, 
            text=True
        )
        
        running_syncs = 0
        for line in ps_result.stdout.splitlines():
            if "sync_images.py" in line or "sync_pdfs.py" in line or "startup_sync.py" in line:
                if "grep" not in line:  # Exclude the grep command itself
                    running_syncs += 1
                    logger.info(f"Found running sync process: {line.strip()}")
        
        if running_syncs > 0:
            logger.info(f"There are {running_syncs} sync processes still running.")
            if "--force" in sys.argv:
                logger.warning("Force flag set, removing lock file despite running processes.")
            else:
                logger.info("Use --force to remove the lock file anyway.")
                return 1
        
        # Remove the lock file
        try:
            os.remove(lock_file)
            logger.info(f"Successfully removed lock file ({lock_age:.1f}s old)")
            return 0
        except Exception as e:
            logger.error(f"Failed to remove lock file: {str(e)}")
            return 1
            
    except Exception as e:
        logger.error(f"Error checking lock file: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = cleanup_lock_files()
    sys.exit(exit_code)