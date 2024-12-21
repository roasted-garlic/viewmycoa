import os
import uuid
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
        'Authorization': f'Bearer {os.environ.get("SQUARE_ACCESS_TOKEN")}',
        'Accept': 'application/json'
    }

    try:
        # Read image file
        with open(image_path, 'rb') as image_file:
            files = {
                'image_file': (os.path.basename(image_path), image_file, 'image/jpeg'),
                'idempotency_key': (None, str(uuid.uuid4()), 'text/plain')
            }
            
            # Make request to Square API
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            
            # Extract image ID from response
            image_data = response.json()
            if 'image' in image_data and 'id' in image_data['image']:
                square_image_id = image_data['image']['id']
                
                # Update product with Square image ID
                product.square_image_id = square_image_id
                db.session.commit()
                
                return square_image_id
                
    except Exception as e:
        print(f"Error uploading image to Square: {str(e)}")
        return None
