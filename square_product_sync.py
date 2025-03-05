import uuid
import json
import requests
from flask import jsonify
from app import app
from models import db, Product, Settings

SQUARE_VERSION = "2024-12-18"

def get_square_headers():
    # Direct database debug - bypassing Settings.get_settings()
    from flask_sqlalchemy import SQLAlchemy
    from models import Settings
    
    app.logger.info("Starting Square headers generation process")
    
    # Direct SQL query to inspect settings table
    import sqlalchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Get database URI from app config
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    app.logger.info(f"Database URI from config: {db_uri}")
    
    # Create a new engine and session
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Direct raw SQL query to debug
    try:
        result = session.execute(text("SELECT id, square_environment, square_sandbox_access_token, square_sandbox_location_id, square_production_access_token, square_production_location_id FROM settings LIMIT 1"))
        row = result.fetchone()
        if row:
            app.logger.info(f"Raw Settings Row: {row}")
            
            # Extract values for easier debugging
            env = row[1]
            sandbox_token = row[2]
            sandbox_location = row[3]
            prod_token = row[4]
            prod_location = row[5]
            
            app.logger.info(f"Environment: {env}")
            app.logger.info(f"Sandbox token present: {bool(sandbox_token)}")
            app.logger.info(f"Sandbox location present: {bool(sandbox_location)}")
            app.logger.info(f"Production token present: {bool(prod_token)}")
            app.logger.info(f"Production location present: {bool(prod_location)}")
            
            # Determine which credentials to use
            if env == 'production' and prod_token and prod_location:
                app.logger.info("Using production credentials from direct SQL")
                return {
                    'Square-Version': SQUARE_VERSION,
                    'Authorization': f'Bearer {prod_token}',
                    'Content-Type': 'application/json'
                }
            elif env != 'production' and sandbox_token and sandbox_location:
                app.logger.info("Using sandbox credentials from direct SQL")
                return {
                    'Square-Version': SQUARE_VERSION,
                    'Authorization': f'Bearer {sandbox_token}',
                    'Content-Type': 'application/json'
                }
            else:
                app.logger.error("Credentials exist but don't match environment setting")
                # Return minimal headers without authorization token
                return {
                    'Square-Version': SQUARE_VERSION,
                    'Content-Type': 'application/json'
                }
        else:
            app.logger.error("No settings row found in database")
            # Return minimal headers without authorization token
            return {
                'Square-Version': SQUARE_VERSION,
                'Content-Type': 'application/json'
            }
    except Exception as e:
        app.logger.error(f"SQL exception when querying Settings: {str(e)}")
        # Return minimal headers without authorization token
        return {
            'Square-Version': SQUARE_VERSION,
            'Content-Type': 'application/json'
        }
    finally:
        session.close()

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

    # Get settings and log information about the product
    app.logger.info(f"Starting sync for product {product.id} - {product.title} with SKU {product.sku}")
    
    # Get required headers for Square API
    headers = get_square_headers()
    if 'Authorization' not in headers:
        app.logger.error("No authorization header available for Square API")
        return {"error": "Square credentials are not configured or invalid. Please set up your Square integration in Settings.", "needs_setup": True}
    
    # Determine base URL and location ID from settings
    settings = Settings.get_settings()
    
    # Directly check the settings values to determine which environment
    if settings.square_environment == 'production':
        base_url = 'https://connect.squareup.com'
        location_id = settings.square_production_location_id
    else:
        base_url = 'https://connect.squareupsandbox.com'
        location_id = settings.square_sandbox_location_id
    
    app.logger.info(f"Using Square base URL: {base_url}")
    app.logger.info(f"Using location ID: {location_id}")
    
    SQUARE_API_URL = f"{base_url}/v2/catalog/object"

    idempotency_key = str(uuid.uuid4())

    if not location_id:
        app.logger.error("Square location ID not configured")
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
            # Use the base_url we determined earlier instead of credentials to avoid None issues
            response = requests.get(
                f"{base_url}/v2/catalog/object/{existing_id}",
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

        # Get headers directly from our improved function
        headers = get_square_headers()
        
        # If no authorization header, we can't make the deletion request
        if 'Authorization' not in headers:
            app.logger.error("No Square authorization available for deletion")
            return {"success": True, "warning": "Product unlinked locally but not deleted from Square due to missing credentials"}
        
        # Determine base URL from settings
        settings = Settings.get_settings()
        if settings.square_environment == 'production':
            base_url = 'https://connect.squareup.com'
        else:
            base_url = 'https://connect.squareupsandbox.com'
            
        # Delete catalog item (will also delete associated images)
        try:
            delete_url = f"{base_url}/v2/catalog/object/{square_id}"
            app.logger.info(f"Square delete URL: {delete_url}")
            
            response = requests.delete(
                delete_url,
                headers=headers
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