import uuid
import json
import requests
from flask import jsonify
from app import app
from models import db, Product, Settings

SQUARE_VERSION = "2024-12-18"

def get_square_headers():
    settings = Settings.get_settings()
    credentials = settings.get_active_square_credentials()
    return {
        'Square-Version': SQUARE_VERSION,
        'Authorization': f'Bearer {credentials["access_token"]}',
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
    from square_category_sync import sync_category_to_square

    settings = Settings.get_settings()
    credentials = settings.get_active_square_credentials()
    
    if not credentials:
        return {"error": "Square credentials are not configured. Please set up your Square integration in Settings.", "needs_setup": True}
        
    SQUARE_API_URL = f"{credentials['base_url']}/v2/catalog/object"

    idempotency_key = str(uuid.uuid4())
    location_id = credentials['location_id']

    if not location_id:
        return {"error": "Square location ID not configured"}

    # Check if product has a category with Square ID
    category_id = None
    if product.categories and len(product.categories) > 0:
        category = product.categories[0]
        if category.square_category_id:
            # Use existing Square category ID
            category_id = category.square_category_id
        else:
            # Only sync category if it doesn't have a Square ID
            category_result = sync_category_to_square(category)
            if 'error' in category_result:
                return {"error": f"Failed to sync category: {category_result['error']}"}
            category_id = category.square_category_id

    existing_id = product.square_catalog_id

    # First sync product without image
    product.square_image_id = None
    db.session.commit()

    # If updating existing item, fetch current version
    current_version = 0
    if existing_id:
        try:
            response = requests.get(
                f"{credentials['base_url']}/v2/catalog/object/{existing_id}",
                headers=get_square_headers()
            )
            if response.status_code == 200:
                current_version = response.json().get('object', {}).get('version', 0)
        except requests.exceptions.RequestException:
            pass

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
            "sku": product.sku,
            "upc": product.barcode,
            "pricing_type": "FIXED_PRICING" if product.price else "VARIABLE_PRICING",
            "price_money": format_price_money(product.price) if product.price else None,
            # ALWAYS include track_inventory as true to ensure Square maintains inventory
            "track_inventory": True,
            "item_option_values": []
        }
    }
    
    # If this is an existing product, fetch the current inventory counts
    if existing_id:
        try:
            # Get the current variation ID from the Square API
            variation_response = requests.get(
                f"{credentials['base_url']}/v2/catalog/object/{existing_id}",
                headers=get_square_headers()
            )
            
            if variation_response.status_code == 200:
                variation_data = variation_response.json().get('object', {})
                # Extract the first variation ID
                if 'item_data' in variation_data and 'variations' in variation_data['item_data'] and len(variation_data['item_data']['variations']) > 0:
                    existing_variation = variation_data['item_data']['variations'][0]
                    
                    # Get the current inventory counts for this variation
                    inventory_response = requests.get(
                        f"{credentials['base_url']}/v2/inventory/{existing_variation['id']}",
                        headers=get_square_headers()
                    )
                    
                    app.logger.info(f"Fetched existing inventory data: {inventory_response.text}")
        except Exception as e:
            app.logger.error(f"Error fetching inventory data: {str(e)}")

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
                "image_ids": [product.square_image_id] if product.square_image_id else [],
                "categories": [{"id": product.categories[0].square_category_id}] if product.categories and len(product.categories) > 0 and product.categories[0].square_category_id else []
            }
        }
    }

    try:
        # Log the API request
        app.logger.info(f"Square API Request URL: {SQUARE_API_URL}")
        app.logger.info(f"Square API Request Headers: {get_square_headers()}")
        app.logger.info(f"Square API Request Body: {json.dumps(product_data, indent=2)}")

        response = requests.post(
            SQUARE_API_URL,
            headers=get_square_headers(),
            json=product_data
        )

        # Log the API response
        app.logger.info(f"Square API Response Status: {response.status_code}")
        app.logger.info(f"Square API Response Body: {response.text}")

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

            # Now handle image upload with the product's Square catalog ID
            if product.product_image:
                from square_image_upload import upload_product_image_to_square
                image_result = upload_product_image_to_square(product)
                if not image_result:
                    return {"error": "Failed to upload product image to Square"}

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
    """Delete a product and its image from Square catalog, preserving categories"""
    if not product.square_catalog_id:
        return {"error": "No Square catalog ID found"}

    try:
        # Store IDs and clear them first
        square_id = product.square_catalog_id
        image_id = product.square_image_id
        product.square_catalog_id = None
        product.square_image_id = None
        # We intentionally do not clear category IDs here to preserve them
        db.session.commit()

        settings = Settings.get_settings()
        credentials = settings.get_active_square_credentials()

        # Delete catalog item (will also delete associated images)
        response = requests.delete(
            f"{credentials['base_url']}/v2/catalog/object/{square_id}",
            headers=get_square_headers()
        )

        # Even if Square returns 404, we've already cleared the IDs locally
        if response.status_code in [200, 404]:
            return {"success": True}
        else:
            # If other error, restore the IDs
            product.square_catalog_id = square_id
            product.square_image_id = image_id
            db.session.commit()
            return {"error": f"Square API error: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}