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
        app.logger.warning("No product image to upload")
        return None

    # Construct full path to image
    image_path = os.path.join('static', product.product_image)
    if not os.path.exists(image_path):
        app.logger.error(f"Image file not found at path: {image_path}")
        return None

    # Get Square API credentials from database
    settings = Settings.get_settings()
    credentials = settings.get_active_square_credentials()

    if not credentials or not credentials.get('access_token'):
        app.logger.error("Square API credentials not configured")
        return None

    url = f"{credentials['base_url']}/v2/catalog/images"
    headers = {
        'Square-Version': '2024-12-18',
        'Authorization': f'Bearer {credentials["access_token"]}'
    }

    try:
        # Clear any existing image ID
        product.square_image_id = None
        db.session.commit()

        # Use product ID and SKU as consistent idempotency key
        idempotency_key = f"{product.id}_{product.sku}_image_{uuid.uuid4()}"

        # Read image file
        with open(image_path, 'rb') as image_file:
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

            app.logger.info(f"Square Image Upload URL: {url}")
            app.logger.debug(f"Square Image Upload Headers: {headers}")
            app.logger.debug(f"Square Image Upload Request JSON: {json.dumps(request_json, indent=2)}")

            response = requests.post(url, headers=headers, files=files)

            app.logger.info(f"Square Image Upload Response Status: {response.status_code}")
            app.logger.debug(f"Square Image Upload Response: {response.text}")

            if response.status_code != 200:
                app.logger.error(f"Error response from Square: {response.text}")
                return None

            result = response.json()
            if 'image' in result and 'id' in result['image']:
                square_image_id = result['image']['id']
                product.square_image_id = square_image_id
                db.session.commit()
                return square_image_id

            app.logger.error("No image ID in Square response")
            return None

    except Exception as e:
        app.logger.error(f"Error uploading image to Square: {str(e)}")
        return None