
import time
import os
import logging
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScheduledSync")

def run_sync():
    """Run both image and PDF sync operations"""
    logger.info("Starting scheduled sync operations")
    
    try:
        # Run image sync
        logger.info("Running image sync...")
        img_result = subprocess.run(
            [sys.executable, "sync_images.py"],
            capture_output=True,
            text=True
        )
        if img_result.returncode == 0:
            logger.info("Image sync completed successfully")
            logger.debug(f"Image sync output: {img_result.stdout}")
        else:
            logger.error(f"Image sync failed: {img_result.stderr}")
            
        # Small delay between operations
        time.sleep(2)
        
        # Run PDF sync
        logger.info("Running PDF sync...")
        pdf_result = subprocess.run(
            [sys.executable, "sync_pdfs.py"],
            capture_output=True,
            text=True
        )
        if pdf_result.returncode == 0:
            logger.info("PDF sync completed successfully")
            logger.debug(f"PDF sync output: {pdf_result.stdout}")
        else:
            logger.error(f"PDF sync failed: {pdf_result.stderr}")
            
        logger.info("Scheduled sync operations completed")
        return True
    except Exception as e:
        logger.error(f"Error during scheduled sync: {str(e)}")
        return False

def run_scheduler(interval_minutes=30):
    """Run sync operations at regular intervals"""
    logger.info(f"Starting sync scheduler with {interval_minutes} minute interval")
    
    try:
        while True:
            run_sync()
            logger.info(f"Waiting {interval_minutes} minutes until next sync...")
            # Sleep for the specified interval
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")

if __name__ == "__main__":
    # Get interval from command line args or use default (30 minutes)
    interval = 30
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        interval = int(sys.argv[1])
    
    # Run the scheduler
    run_scheduler(interval)
