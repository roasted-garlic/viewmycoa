import os
import uuid
import requests
from flask import jsonify
from app import app
from models import db, Category

SQUARE_BASE_URL = os.environ.get("SQUARE_BASE_URL", "https://connect.squareup.com")
SQUARE_API_URL = f"{SQUARE_BASE_URL}/v2/catalog/object"
SQUARE_VERSION = "2024-12-18"

def get_square_headers():
    return {
        'Square-Version': SQUARE_VERSION,
        'Authorization': f'Bearer {os.environ.get("SQUARE_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }

def sync_category_to_square(category):
    """Sync a single category to Square catalog"""
    idempotency_key = str(uuid.uuid4())
    
    # Prepare the category data
    category_data = {
        "idempotency_key": idempotency_key,
        "object": {
            "type": "CATEGORY",
            "id": f"#{category.id}" if not category.square_category_id else category.square_category_id,
            "category_data": {
                "name": category.name
            }
        }
    }
    
    try:
        response = requests.post(
            SQUARE_API_URL,
            headers=get_square_headers(),
            json=category_data
        )
        
        if response.status_code == 401:
            return {"error": "Square API authentication failed. Please verify your access token."}
        elif response.status_code != 200:
            return {"error": f"Square API error: {response.text}"}
            
        result = response.json()
        
        # Store the Square category ID
        catalog_object = result.get('catalog_object', {})
        if catalog_object and catalog_object.get('id'):
            category.square_category_id = catalog_object['id']
            db.session.commit()
            
        return result
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_category_from_square(category):
    """Delete a category from Square catalog"""
    if not category.square_category_id:
        return {"error": "No Square category ID found"}
        
    try:
        # Store ID and clear it first
        square_id = category.square_category_id
        category.square_category_id = None
        db.session.commit()
        
        # Delete catalog item
        response = requests.delete(
            f"{SQUARE_BASE_URL}/v2/catalog/object/{square_id}",
            headers=get_square_headers()
        )
        
        # Even if Square returns 404, we've already cleared the ID locally
        if response.status_code in [200, 404]:
            return {"success": True}
        else:
            # If other error, restore the ID
            category.square_category_id = square_id
            db.session.commit()
            return {"error": f"Square API error: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def sync_all_categories():
    """Sync all categories to Square catalog"""
    categories = Category.query.all()
    results = []
    
    for category in categories:
        result = sync_category_to_square(category)
        results.append({
            "category_id": category.id,
            "name": category.name,
            "result": result
        })
    
    return results
