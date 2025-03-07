
import os
import requests
import logging
from flask import url_for
from models import Product, db, GeneratedPDF

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AutoSync")

# Define the base URL of your development site
# This should be your Replit development URL
DEV_ENDPOINT = "https://repl-viewmycoa.replit.app"  # Make sure this matches your Replit URL

def trigger_image_sync(product_id):
    """
    Trigger image sync for a specific product ID when an image is uploaded in production
    Args:
        product_id: The ID of the product that had an image uploaded
    """
    try:
        logger.info(f"Triggering image sync for product ID: {product_id}")
        
        # Make request to development server sync endpoint
        response = requests.post(
            f"{DEV_ENDPOINT}/api/sync/images", 
            json={"product_ids": [product_id]},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully triggered image sync for product ID {product_id}")
            return True
        else:
            logger.error(f"Failed to trigger image sync. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering image sync: {str(e)}")
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
        response = requests.post(
            f"{DEV_ENDPOINT}/api/sync/pdfs", 
            json={"product_ids": [product_id]},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully triggered PDF sync for product ID {product_id}")
            return True
        else:
            logger.error(f"Failed to trigger PDF sync. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering PDF sync: {str(e)}")
        return False
