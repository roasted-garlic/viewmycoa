
import os
import uuid
import requests
from flask import jsonify
from app import app
from models import db, Product

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
    
    # If updating existing item, fetch current version first
    current_version = 0
    if existing_id:
        try:
            response = requests.get(
                f"{SQUARE_BASE_URL}/v2/catalog/object/{existing_id}",
                headers=get_square_headers()
            )
            if response.status_code == 200:
                current_version = response.json().get('object', {}).get('version', 0)
        except requests.exceptions.RequestException:
            pass

    # Handle image upload first if needed
    if product.product_image and not product.square_image_id:
        from square_image_upload import upload_product_image_to_square
        upload_product_image_to_square(product)
        
    # Create product data structure
    sku_id = f"#{product.sku}"
    variation_id = f"#{product.sku}_regular"
    
    # Create variation data with ID for both new and existing items
    variation_data = {
        "type": "ITEM_VARIATION",
        "id": variation_id,
        "item_variation_data": {
            "item_id": existing_id if existing_id else sku_id,
            "name": "Regular",
            "pricing_type": "FIXED_PRICING" if product.price else "VARIABLE_PRICING",
            "price_money": format_price_money(product.price) if product.price else None
        }
    }
        
    product_data = {
        "idempotency_key": idempotency_key,
        "object": {
            "type": "ITEM",
            "id": existing_id if existing_id else sku_id,
            "version": current_version,
            "present_at_location_ids": [location_id],
            "item_data": {
                "name": product.title,
                "description": next(iter(product.get_attributes().values()), ""),
                "variations": [variation_data],
                "image_ids": [product.square_image_id] if product.square_image_id else []
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
        catalog_object = result.get('catalog_object', {})
        if catalog_object and catalog_object.get('id'):
            product.square_catalog_id = catalog_object['id']
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

def delete_product_from_square(product):
    """Delete a product from Square catalog"""
    if not product.square_catalog_id:
        return {"error": "No Square catalog ID found"}
        
    try:
        # Store the ID and clear it first
        square_id = product.square_catalog_id
        product.square_catalog_id = None
        db.session.commit()
        
        response = requests.delete(
            f"{SQUARE_BASE_URL}/v2/catalog/object/{square_id}",
            headers=get_square_headers()
        )
        
        # Even if Square returns 404, we've already cleared the ID locally
        if response.status_code in [200, 404]:
            return {"success": True}
        else:
            # If other error, restore the ID
            product.square_catalog_id = square_id
            db.session.commit()
            return {"error": f"Square API error: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
