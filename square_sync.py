import os
import uuid
import requests
from app import db
from models import Product

SQUARE_API_URL = "https://connect.squareup.com/v2/catalog/object"
SQUARE_VERSION = "2024-12-18"

def get_square_headers():
    return {
        'Square-Version': SQUARE_VERSION,
        'Authorization': f'Bearer {os.environ.get("SQUARE_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }

def format_price_money(price):
    """Convert float price to Square's integer cents format"""
    if price is None:
        return None
    return {
        "amount": int(price * 100),  # Convert to cents
        "currency": "USD"
    }

def sync_product_to_square(product):
    """Sync a single product to Square catalog"""
    idempotency_key = str(uuid.uuid4())
    
    # Prepare variation for the product
    variation_id = f"#{product.sku}_var" if not product.square_catalog_id else f"{product.square_catalog_id}_var"
    
    # Prepare product data according to Square API format
    product_data = {
        "idempotency_key": idempotency_key,
        "object": {
            "type": "ITEM",
            "id": f"#{product.sku}" if not product.square_catalog_id else product.square_catalog_id,
            "item_data": {
                "name": product.title,
                "description": next(iter(product.get_attributes().values()), ""),
                "abbreviation": product.sku,
                "variations": [
                    {
                        "type": "ITEM_VARIATION",
                        "id": variation_id,
                        "item_variation_data": {
                            "item_id": f"#{product.sku}" if not product.square_catalog_id else product.square_catalog_id,
                            "name": "Regular",
                            "pricing_type": "FIXED_PRICING" if product.price else "VARIABLE_PRICING",
                            "price_money": format_price_money(product.price) if product.price else None,
                            "stockable": True
                        }
                    }
                ],
                "product_type": "REGULAR"
            }
        }
    }

    try:
        response = requests.post(
            SQUARE_API_URL,
            headers=get_square_headers(),
            json=product_data
        )
        response.raise_for_status()
        result = response.json()
        
        # Store the catalog ID from Square's response
        catalog_object = result.get('catalog_object', {})
        if catalog_object and catalog_object.get('id'):
            product.square_catalog_id = catalog_object['id']
            db.session.commit()
            
            # Return success response matching the sample format
            return {
                "success": True,
                "square_id": product.square_catalog_id,
                "response": {
                    "catalog_object": catalog_object,
                    "id_mappings": [
                        {
                            "client_object_id": f"#{product.sku}",
                            "object_id": catalog_object['id']
                        },
                        {
                            "client_object_id": f"#{product.sku}_var",
                            "object_id": f"{catalog_object['id']}_var"
                        }
                    ]
                }
            }
        else:
            return {
                "success": False,
                "error": "No catalog object ID in response",
                "response": result
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def sync_all_products():
    """Sync all products to Square catalog"""
    products = Product.query.all()
    results = []
    
    for product in products:
        result = sync_product_to_square(product)
        results.append({
            "product_id": product.id,
            "sku": product.sku,
            "result": result
        })
    
    return results
