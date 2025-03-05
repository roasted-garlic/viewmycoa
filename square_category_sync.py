import uuid
import requests
from flask import jsonify
from app import app
from models import db, Category, Settings

SQUARE_VERSION = "2024-12-18"

def get_square_headers():
    # Use the same function from square_product_sync to ensure consistent behavior
    from square_product_sync import get_square_headers as product_get_headers
    return product_get_headers()

def sync_category_to_square(category):
    """Sync a single category to Square catalog"""
    # Get headers directly from our improved function
    headers = get_square_headers()
    
    # If no authorization header, we can't proceed
    if 'Authorization' not in headers:
        app.logger.error("No Square authorization available for category sync")
        return {"error": "Square credentials are not configured. Please set up your Square integration in Settings.", "needs_setup": True}
    
    # Determine base URL from settings
    settings = Settings.get_settings()
    if settings.square_environment == 'production':
        base_url = 'https://connect.squareup.com'
    else:
        base_url = 'https://connect.squareupsandbox.com'
    
    SQUARE_API_URL = f"{base_url}/v2/catalog/object"
    app.logger.info(f"Square category sync URL: {SQUARE_API_URL}")
    
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
            headers=headers,
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

        # Get headers directly from our improved function
        headers = get_square_headers()
        
        # If no authorization header, we can't make the deletion request
        if 'Authorization' not in headers:
            app.logger.error("No Square authorization available for category deletion")
            return {"success": True, "warning": "Category unlinked locally but not deleted from Square due to missing credentials"}
        
        # Determine base URL from settings
        settings = Settings.get_settings()
        if settings.square_environment == 'production':
            base_url = 'https://connect.squareup.com'
        else:
            base_url = 'https://connect.squareupsandbox.com'
            
        # Delete catalog item
        try:
            delete_url = f"{base_url}/v2/catalog/object/{square_id}"
            app.logger.info(f"Square category delete URL: {delete_url}")
            
            response = requests.delete(
                delete_url,
                headers=headers
            )
        except Exception as e:
            app.logger.error(f"Exception during Square category deletion: {str(e)}")
            return {"success": True, "warning": f"Category unlinked locally but error occurred during Square deletion: {str(e)}"}

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