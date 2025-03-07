
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
        
        # Make request to development server sync endpoint
        endpoint = f"{DEV_ENDPOINT}/api/sync/images"
        logger.info(f"Sending request to endpoint: {endpoint}")
        
        response = requests.post(
            endpoint, 
            json={"product_ids": [product_id]},
            timeout=30
        )
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"Successfully triggered image sync for product ID {product_id}")
            return True
        else:
            logger.error(f"Failed to trigger image sync. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            # Try another attempt with a different protocol if https fails
            if "https" in DEV_ENDPOINT:
                alt_endpoint = DEV_ENDPOINT.replace("https", "http")
                logger.info(f"Trying alternative endpoint: {alt_endpoint}/api/sync/images")
                alt_response = requests.post(
                    f"{alt_endpoint}/api/sync/images",
                    json={"product_ids": [product_id]},
                    timeout=30
                )
                if alt_response.status_code == 200:
                    logger.info(f"Successfully triggered image sync using alternative endpoint")
                    return True
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
        
        # Make request to development server sync endpoint
        endpoint = f"{DEV_ENDPOINT}/api/sync/pdfs"
        logger.info(f"Sending request to endpoint: {endpoint}")
        
        response = requests.post(
            endpoint, 
            json={"product_ids": [product_id]},
            timeout=30  # Extended timeout for PDF transfer
        )
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"Successfully triggered PDF sync for product ID {product_id}")
            return True
        else:
            logger.error(f"Failed to trigger PDF sync. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            # Try another attempt with a different protocol if https fails
            if "https" in DEV_ENDPOINT:
                alt_endpoint = DEV_ENDPOINT.replace("https", "http")
                logger.info(f"Trying alternative endpoint: {alt_endpoint}/api/sync/pdfs")
                alt_response = requests.post(
                    f"{alt_endpoint}/api/sync/pdfs",
                    json={"product_ids": [product_id]},
                    timeout=30
                )
                if alt_response.status_code == 200:
                    logger.info(f"Successfully triggered PDF sync using alternative endpoint")
                    return True
            return False
            
    except Exception as e:
        logger.error(f"Error triggering PDF sync: {str(e)}")
        # Add traceback for better debugging
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False
