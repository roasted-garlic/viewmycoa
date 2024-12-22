
import os
import uuid
import json
import requests
from typing import Optional
from models import Product, db

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

    # Square API endpoint and headers
    SQUARE_BASE_URL = os.environ.get("SQUARE_BASE_URL", "https://connect.squareup.com")
    url = f"{SQUARE_BASE_URL}/v2/catalog/images"
    headers = {
        'Square-Version': '2024-12-18',
        'Authorization': f'Bearer {os.environ.get("SQUARE_ACCESS_TOKEN")}'
    }

    try:
        # Use product ID and SKU as consistent idempotency key
        idempotency_key = f"{product.id}_{product.sku}_image"
        
        # Read image file
        with open(image_path, 'rb') as image_file:
            
            # Create request data following Square's format
            unique_image_id = f'#{product.id}_{product.sku}_image_{idempotency_key}'
            request_data = {
                'idempotency_key': idempotency_key,
                'object_id': None,
                'image': {
                    'type': 'IMAGE',
                    'id': unique_image_id,
                    'image_data': {
                        'caption': product.title
                    }
                }
            }
            
            # Prepare multipart form data
            request_json = {
                "idempotency_key": idempotency_key,
                "object_id": None,
                "image": {
                    "type": "IMAGE",
                    "id": unique_image_id,
                    "image_data": {
                        "caption": product.title
                    }
                }
            }
            
            files = {
                'request': ('', json.dumps(request_json), 'application/json'),
                'image_file': (os.path.basename(image_path), image_file, 'image/png')
            }
            
            # Make request to Square API
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code != 200:
                print(f"Error response from Square: {response.text}")
                return None
                
            # Extract image ID from response
            result = response.json()
            if 'image' in result and 'id' in result['image']:
                square_image_id = result['image']['id']
                product.square_image_id = square_image_id
                db.session.commit()
                return square_image_id

            # If we get here, the upload failed without an exception
            product.square_image_id = None
            db.session.commit()
            return None
                
    except Exception as e:
        print(f"Error uploading image to Square: {str(e)}")
        # Clear the image ID on error
        product.square_image_id = None
        db.session.commit()
        return None
