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
    
    # Ensure we have valid credentials before accessing them
    if not credentials:
        app.logger.error("No Square credentials found. Cannot generate headers.")
        # Return minimal headers without authorization token
        return {
            'Square-Version': SQUARE_VERSION,
            'Content-Type': 'application/json'
        }
        
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

    # Log credential status for debugging
    app.logger.info(f"Square credentials check: {bool(credentials)}")
    
    if not credentials:
        app.logger.error("Square credentials not found or invalid")
        return {"error": "Square credentials are not configured. Please set up your Square integration in Settings.", "needs_setup": True}
    
    # Validate required credentials fields
    if not credentials.get('access_token') or not credentials.get('location_id') or not credentials.get('base_url'):
        app.logger.error(f"Incomplete Square credentials: access_token: {bool(credentials.get('access_token'))}, location_id: {bool(credentials.get('location_id'))}, base_url: {bool(credentials.get('base_url'))}")
        return {"error": "Square credentials are incomplete. Please check your Square integration in Settings.", "needs_setup": True}

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

    # If updating existing item, fetch current version and variation ID
    current_version = 0
    existing_variation_id = None
    
    if existing_id:
        try:
            response = requests.get(
                f"{credentials['base_url']}/v2/catalog/object/{existing_id}",
                headers=get_square_headers()
            )
            if response.status_code == 200:
                item_data = response.json().get('object', {})
                current_version = item_data.get('version', 0)
                
                # Extract the actual variation ID from the response
                variations = item_data.get('item_data', {}).get('variations', [])
                if variations and len(variations) > 0:
                    existing_variation_id = variations[0].get('id')
                    # Store this variation ID for future use
                    if existing_variation_id:
                        product.square_variation_id = existing_variation_id
                        db.session.commit()
                        app.logger.info(f"Found existing Square variation ID: {existing_variation_id}")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error fetching existing item: {str(e)}")
            pass

    # Create product data structure
    sku_id = f"#{product.sku}"
    
    # Use the existing variation ID if we have one, otherwise create a new client-defined ID
    if product.square_variation_id and existing_id:
        # Use the actual Square-assigned variation ID for existing products
        variation_id = product.square_variation_id
        app.logger.info(f"Using stored Square variation ID: {variation_id}")
    else:
        # For new products, use our client-defined ID format
        variation_id = f"#{product.sku}_regular"
        app.logger.info(f"Using new client-defined variation ID: {variation_id}")

    # Create variation data with appropriate ID
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

    # Only add location_overrides for new items, not for updates
    if not existing_id:
        variation_data["item_variation_data"]["location_overrides"] = [{
            "location_id": location_id
        }]

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
        elif response.status_code == 400:
            # Check for version mismatch error specifically
            error_body = response.json()
            errors = error_body.get('errors', [])
            
            for error in errors:
                if error.get('code') == 'VERSION_MISMATCH':
                    app.logger.info("Detected version mismatch, fetching latest version and retrying")
                    
                    # Fetch the latest version
                    try:
                        refresh_response = requests.get(
                            f"{credentials['base_url']}/v2/catalog/object/{existing_id}",
                            headers=get_square_headers()
                        )
                        
                        if refresh_response.status_code == 200:
                            latest_item = refresh_response.json().get('object', {})
                            latest_version = latest_item.get('version', 0)
                            
                            # Update product_data with latest version and retry
                            product_data['object']['version'] = latest_version
                            
                            # Retry the request
                            app.logger.info(f"Retrying with version {latest_version}")
                            retry_response = requests.post(
                                SQUARE_API_URL,
                                headers=get_square_headers(),
                                json=product_data
                            )
                            
                            if retry_response.status_code == 200:
                                return retry_response.json()
                            else:
                                app.logger.error(f"Retry failed: {retry_response.text}")
                                return {"error": f"Square API error on retry: {retry_response.text}"}
                    except Exception as retry_error:
                        app.logger.error(f"Error during version mismatch retry: {str(retry_error)}")
                        return {"error": f"Error during version mismatch handling: {str(retry_error)}"}
            
            # If we get here, it's a different 400 error
            return {"error": f"Square API error: {response.text}"}
        elif response.status_code != 200:
            return {"error": f"Square API error: {response.text}"}

        result = response.json()

        # Store the catalog ID from Square's response
        catalog_object = result.get('catalog_object', {})
        id_mappings = result.get('id_mappings', [])
        
        if catalog_object and catalog_object.get('id'):
            product.square_catalog_id = catalog_object['id']
            
            # Look for variation ID in the response mappings
            for mapping in id_mappings:
                client_id = mapping.get('client_object_id')
                object_id = mapping.get('object_id')
                
                # If this is a variation ID mapping
                if client_id and object_id and client_id.endswith('_regular'):
                    app.logger.info(f"Found variation ID mapping: {client_id} -> {object_id}")
                    product.square_variation_id = object_id
                    break
            
            # If we couldn't find it in mappings, try to extract from the response object directly
            if not product.square_variation_id:
                variations = catalog_object.get('item_data', {}).get('variations', [])
                if variations and len(variations) > 0:
                    variation_id = variations[0].get('id')
                    if variation_id:
                        app.logger.info(f"Found variation ID in response: {variation_id}")
                        product.square_variation_id = variation_id
            
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
        variation_id = product.square_variation_id
        product.square_catalog_id = None
        product.square_image_id = None
        product.square_variation_id = None
        # We intentionally do not clear category IDs here to preserve them
        db.session.commit()

        settings = Settings.get_settings()
        credentials = settings.get_active_square_credentials()
        
        # If we don't have credentials, report an error but still clear local IDs
        if not credentials:
            app.logger.error("Failed to get Square credentials for deletion")
            return {"success": True, "warning": "Product unlinked locally but not deleted from Square due to missing credentials"}
            
        # Delete catalog item (will also delete associated images)
        try:
            response = requests.delete(
                f"{credentials['base_url']}/v2/catalog/object/{square_id}",
                headers=get_square_headers()
            )
        except Exception as e:
            app.logger.error(f"Exception during Square deletion: {str(e)}")
            return {"success": True, "warning": f"Product unlinked locally but error occurred during Square deletion: {str(e)}"}

        # Even if Square returns 404, we've already cleared the IDs locally
        if response.status_code in [200, 404]:
            return {"success": True}
        else:
            # If other error, restore the IDs
            product.square_catalog_id = square_id
            product.square_image_id = image_id
            product.square_variation_id = variation_id
            db.session.commit()
            return {"error": f"Square API error: {response.text}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}