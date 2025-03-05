import uuid
import json
import requests
import logging
import datetime
import os
from typing import Optional
from models import Product, db, Settings
from app import app

def upload_product_image_to_square(product: Product) -> Optional[str]:
    """
    Upload a product's image to Square Catalog API.
    Args:
        product: Product instance with product_image path
    Returns:
        str: Square image ID if successful, None otherwise
    """
    if not product.product_image:
        return None

    # Construct full path to image
    image_path = os.path.join('static', product.product_image)
    if not os.path.exists(image_path):
        return None

    # Get Square API credentials - use the direct approach for consistency
    # First from square_product_sync to ensure consistent behavior
    from square_product_sync import get_square_headers
    
    app.logger.info("Getting Square credentials for image upload")
    
    # Get headers using the same function for all Square API calls
    headers = get_square_headers()
    
    # Check if we have valid headers with authorization
    if 'Authorization' not in headers:
        app.logger.error("No Square authorization available for image upload")
        return None
    
    # Get settings to determine base URL
    settings = Settings.get_settings()
    credentials = settings.get_active_square_credentials()
    
    # Fall back to hardcoded URLs if credentials method failed
    if not credentials or 'base_url' not in credentials:
        app.logger.warning("Could not get base_url from credentials, using fallback")
        if settings.square_environment == 'production':
            base_url = 'https://connect.squareup.com'
        else:
            base_url = 'https://connect.squareupsandbox.com'
    else:
        base_url = credentials['base_url']
    
    url = f"{base_url}/v2/catalog/images"
    app.logger.info(f"Square image upload URL: {url}")

    try:
        # Clear any existing image ID
        product.square_image_id = None
        db.session.commit()

        # Use product ID and SKU as consistent idempotency key
        idempotency_key = f"{product.id}_{product.sku}_image_{uuid.uuid4()}"

        # Read image file
        with open(image_path, 'rb') as image_file:
            # Create request data following Square's format
            request_json = {
                "idempotency_key": idempotency_key,
                "object_id": product.square_catalog_id,
                "is_primary": True,
                "image": {
                    "type": "IMAGE",
                    "id": f"#image_{product.id}_{product.sku}_{uuid.uuid4().hex}_{int(datetime.datetime.now().timestamp())}",
                    "image_data": {
                        "name": product.title,
                        "caption": product.title
                    }
                }
            }

            files = {
                'request': ('', json.dumps(request_json), 'application/json'),
                'image_file': (os.path.basename(image_path), image_file, 'image/png')
            }

            # Log the API request
            app.logger.info(f"Square Image Upload URL: {url}")
            app.logger.info(f"Square Image Upload Headers: {headers}")
            app.logger.info(f"Square Image Upload Request JSON: {json.dumps(request_json, indent=2)}")

            # Make request to Square API
            response = requests.post(url, headers=headers, files=files)

            # Log the API response
            app.logger.info(f"Square Image Upload Response Status: {response.status_code}")
            app.logger.info(f"Square Image Upload Response: {response.text}")

            if response.status_code != 200:
                app.logger.error(f"Error response from Square: {response.text}")
                return None

            # Extract image ID from response
            result = response.json()
            if 'image' in result and 'id' in result['image']:
                square_image_id = result['image']['id']
                product.square_image_id = square_image_id
                db.session.commit()
                return square_image_id

            product.square_image_id = None
            db.session.commit()
            return None

    except Exception as e:
        app.logger.error(f"Error uploading image to Square: {str(e)}")
        # Include stack trace for better debugging
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        product.square_image_id = None
        db.session.commit()
        return None