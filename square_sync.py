
import os
import uuid
import requests
from flask import jsonify
from app import db, app
from models import Product

SQUARE_BASE_URL = os.environ.get("SQUARE_BASE_URL", "https://connect.squareup.com")
SQUARE_API_URL = f"{SQUARE_BASE_URL}/v2/catalog/object"
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
    location_id = os.environ.get('SQUARE_LOCATION_ID')
    
    if not location_id:
        return {"error": "Square location ID not configured"}
    
    existing_id = product.square_catalog_id
    
    # Create product data structure
    product_data = {
        "idempotency_key": idempotency_key,
        "object": {
            "type": "ITEM",
            "id": existing_id if existing_id else f"#{product.sku}",
            "present_at_location_ids": [location_id],
            "item_data": {
                "name": product.title,
                "description": next(iter(product.get_attributes().values()), ""),
                "variations": [{
                    "type": "ITEM_VARIATION",
                    "id": f"#{product.sku}_regular",
                    "item_variation_data": {
                        "item_id": f"#{product.sku}",
                        "name": "Regular",
                        "pricing_type": "FIXED_PRICING" if product.price else "VARIABLE_PRICING",
                        "price_money": format_price_money(product.price) if product.price else None
                    }
                }]
            }
        }
    }

    try:
        response = requests.post(
            SQUARE_API_URL,
            headers=get_square_headers(),
            json=product_data
        )
        if response.status_code == 401:
            return {"error": "Square API authentication failed. Please verify your access token."}
        elif response.status_code != 200:
            return {"error": f"Square API error: {response.text}"}
            
        result = response.json()
        
        # Store the catalog ID from Square's response
        if result.get('object') and result['object'].get('id'):
            product.square_catalog_id = result['object']['id']
            db.session.commit()
            
        return result
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

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


