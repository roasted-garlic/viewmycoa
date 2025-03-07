
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
    
    This function is DEPRECATED - sync is now only performed at development server startup,
    not triggered by production events.
    
    Args:
        product_id: The ID of the product that had an image uploaded
    """
    # This function is now a no-op in both environments.
    # The design has changed to only sync on development server startup.
    logger.info(f"Image sync triggered for product ID {product_id} - IGNORED (sync now only happens on development startup)")
    return True

def trigger_pdf_sync(product_id):
    """
    Trigger PDF sync for a specific product ID when a PDF is generated in production
    
    This function is DEPRECATED - sync is now only performed at development server startup,
    not triggered by production events.
    
    Args:
        product_id: The ID of the product that had a PDF generated
    """
    # This function is now a no-op in both environments.
    # The design has changed to only sync on development server startup.
    logger.info(f"PDF sync triggered for product ID {product_id} - IGNORED (sync now only happens on development startup)")
    return True
