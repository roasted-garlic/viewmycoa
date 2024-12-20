
import os
import uuid
import requests
from flask import jsonify
from app import db, app
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
    location_id = os.environ.get('SQUARE_LOCATION_ID')
    
    if not location_id:
        return {"error": "Square location ID not configured"}
    
    existing_id = product.square_catalog_id
    if existing_id:
        # Use existing ID if available
        product_data = {
            "idempotency_key": idempotency_key,
            "object": {
                "id": existing_id,
                "type": "ITEM",
                "version": 1,  # Increment version for update
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
            "type": "ITEM",
            "item_data": {
                "name": product.title,
                "description": next(iter(product.get_attributes().values()), ""),
                "variations": [
                    {
                        "id": f"#{product.sku}_regular",
                        "type": "ITEM_VARIATION",
                        "item_variation_data": {
                            "item_id": f"#{product.sku}",
                            "name": "Regular",
                            "pricing_type": "FIXED_PRICING" if product.price else "VARIABLE_PRICING",
                            "price_money": format_price_money(product.price) if product.price else None
                        }
                    }
                ]
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

@app.route('/api/square/sync/<int:product_id>', methods=['POST'])
def sync_single_product(product_id):
    """Sync a single product to Square"""
    try:
        product = Product.query.get_or_404(product_id)
        result = sync_product_to_square(product)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        app.logger.error(f"Error syncing product to Square: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
