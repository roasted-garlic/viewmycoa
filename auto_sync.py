
import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutoSync")

# Define endpoints
DEV_ENDPOINT = "http://localhost:3000"  # Development server endpoint

def trigger_image_sync(product_id):
    """
    Trigger image sync for a specific product ID when an image is uploaded in production
    Args:
        product_id: The ID of the product that had an image uploaded
    """
    try:
        logger.info(f"Triggering image sync for product ID: {product_id}")
        
        # Check if we're trying to sync with ourselves (which would be redundant)
        # This can happen if both production and dev environments try to sync with each other
        if os.environ.get("REPLIT_DEPLOYMENT", "0") != "1":
            logger.info(f"Skipping image sync in development environment")
            return True
            
        # Make request to development server sync endpoint
        endpoint = f"{DEV_ENDPOINT}/api/sync/images"
        logger.info(f"Sending request to endpoint: {endpoint}")
        
        # Make multiple attempts with different protocols and timeouts
        try:
            response = requests.post(
                endpoint, 
                json={"product_ids": [product_id]},
                timeout=30
            )
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Successfully triggered image sync for product ID {product_id}")
                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"First attempt failed: {str(e)}")
            
        # Try with alternative protocol
        if "https" in DEV_ENDPOINT:
            alt_endpoint = DEV_ENDPOINT.replace("https", "http")
            logger.info(f"Trying alternative endpoint: {alt_endpoint}/api/sync/images")
            try:
                alt_response = requests.post(
                    f"{alt_endpoint}/api/sync/images",
                    json={"product_ids": [product_id]},
                    timeout=45  # Extended timeout for retry
                )
                if alt_response.status_code == 200:
                    logger.info(f"Successfully triggered image sync using alternative endpoint")
                    return True
            except requests.exceptions.RequestException as e:
                logger.error(f"Alternative attempt failed: {str(e)}")
        
        # Final attempt with direct IP if available
        try:
            direct_endpoint = "http://0.0.0.0:3000/api/sync/images"
            logger.info(f"Trying direct endpoint: {direct_endpoint}")
            direct_response = requests.post(
                direct_endpoint,
                json={"product_ids": [product_id]},
                timeout=45
            )
            if direct_response.status_code == 200:
                logger.info(f"Successfully triggered image sync using direct endpoint")
                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Direct attempt failed: {str(e)}")
            
        logger.error(f"All sync attempts failed for product ID {product_id}")
        return False
            
    except Exception as e:
        logger.error(f"Error triggering image sync: {str(e)}")
        # Add traceback for better debugging
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

def trigger_pdf_sync(product_id):
    """
    Trigger PDF sync for a specific product ID when a PDF is generated in production
    Args:
        product_id: The ID of the product that had a PDF generated
    """
    try:
        logger.info(f"Triggering PDF sync for product ID: {product_id}")
        
        # Check if we're trying to sync with ourselves (which would be redundant)
        # This can happen if both production and dev environments try to sync with each other
        if os.environ.get("REPLIT_DEPLOYMENT", "0") != "1":
            logger.info(f"Skipping PDF sync in development environment")
            return True
        
        # Fall back to direct script execution if HTTP sync fails
        try:    
            # Make request to development server sync endpoint
            endpoint = f"{DEV_ENDPOINT}/api/sync/pdfs"
            logger.info(f"Sending request to endpoint: {endpoint}")
            
            # Try HTTP sync first with a shorter timeout
            response = requests.post(
                endpoint, 
                json={"product_ids": [product_id]},
                timeout=10  # Shorter timeout - fail faster
            )
            
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Successfully triggered PDF sync for product ID {product_id}")
                return True
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP sync failed: {str(e)}")
        
        # If HTTP sync fails, run the PDF sync script directly via subprocess
        # This is more reliable but requires the production server to have access to the script
        try:
            import subprocess
            import sys
            
            logger.info(f"Attempting direct script execution for product ID: {product_id}")
            
            # Path to the sync_pdfs.py script - adjust if needed
            script_path = "sync_pdfs.py"
            
            # Run the script with the product ID as an argument
            result = subprocess.run(
                [sys.executable, script_path, str(product_id)],
                capture_output=True,
                text=True,
                timeout=120  # 2-minute timeout for script execution
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully executed sync script for product ID {product_id}")
                logger.debug(f"Script output: {result.stdout}")
                return True
            else:
                logger.error(f"Script execution failed with code {result.returncode}: {result.stderr}")
                return False
                
        except Exception as script_error:
            logger.error(f"Error executing sync script: {str(script_error)}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering PDF sync: {str(e)}")
        # Add traceback for better debugging
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False
