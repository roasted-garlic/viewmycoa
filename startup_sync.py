
import os
import logging
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StartupSync")

def run_startup_sync():
    """Run both image and PDF sync operations when the development environment starts"""
    # Only run in development environment
    if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
        logger.info("Skipping startup sync in production environment")
        return

    logger.info("Starting sync operations on development environment startup")
    
    try:
        # Small delay to ensure database and Flask app are initialized
        time.sleep(3)
        
        # Run image sync
        logger.info("Running image sync (download new, remove deleted)...")
        img_result = subprocess.run(
            [sys.executable, "sync_images.py"],
            capture_output=True,
            text=True
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
            text=True
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
        
    except Exception as e:
        logger.error(f"Error during startup sync: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    run_startup_sync()
