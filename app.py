import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import logging
from werkzeug.utils import secure_filename
import requests
import json
from PIL import Image
import datetime
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from utils import generate_batch_number, is_valid_image
from models import db, product_categories, User
from decorators import admin_required

app = Flask(__name__)
migrate = Migrate(app, db)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login route
login_manager.login_message = None  # Disable the default login message
login_manager.login_message_category = 'info'  # Use Bootstrap styling
login_manager.login_message_flashing = False  # Prevent automatic flashing

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configuration for secret key
# IMPORTANT: For production deployment, set FLASK_SECRET_KEY environment variable
if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1" and not os.environ.get("FLASK_SECRET_KEY"):
    app.logger.error("CRITICAL ERROR: FLASK_SECRET_KEY environment variable is not set. Using fallback key (not recommended for production)")

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a development-only secret key"

# Import sys module for exit functionality
import sys

# Database configuration with fallbacks
# The application will use the following database connection in order of priority:
# 1. DATABASE_URL environment variable 
# 2. Constructed from individual PGUSER, PGPASSWORD, etc. variables
# 3. Fallback to SQLite in any environment (including deployment) if no Postgres variables are set

# First, try to get a complete database URL
database_url = os.environ.get("DATABASE_URL")

# Log the environment variables we're checking (redacting sensitive info)
env_vars = {
    "REPLIT_DEPLOYMENT": os.environ.get("REPLIT_DEPLOYMENT", "0"),
    "DATABASE_URL": "***redacted***" if database_url else "Not set",
    "PGDATABASE": os.environ.get("PGDATABASE", "Not set"),
    "PGHOST": os.environ.get("PGHOST", "Not set"),
    "PGPORT": os.environ.get("PGPORT", "Not set"),
    "PGUSER": "***redacted***" if os.environ.get("PGUSER") else "Not set",
    "PGPASSWORD": "***redacted***" if os.environ.get("PGPASSWORD") else "Not set"
}
app.logger.info(f"Database environment check: {env_vars}")

# Handle deployment specially to ensure we detect and fix database issues
if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
    app.logger.warning("DEPLOYMENT MODE DETECTED - Checking database configuration...")

    # If we're in deployment and database_url isn't set, we need to construct it 
    if not database_url:
        app.logger.warning("No DATABASE_URL found in deployment, constructing from individual variables")

        # Make sure these individual variables are present
        pg_user = os.environ.get("PGUSER")
        pg_password = os.environ.get("PGPASSWORD")
        pg_host = os.environ.get("PGHOST") 
        pg_port = os.environ.get("PGPORT")
        pg_database = os.environ.get("PGDATABASE")

        # Check if all PostgreSQL variables are set
        if pg_user and pg_password and pg_host and pg_port and pg_database:
            database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
            app.logger.info("Successfully constructed PostgreSQL URL from environment variables")
        else:
            # Missing variables - this will cause deployment to fail
            missing_vars = []
            if not pg_user: missing_vars.append("PGUSER")
            if not pg_password: missing_vars.append("PGPASSWORD") 
            if not pg_host: missing_vars.append("PGHOST")
            if not pg_port: missing_vars.append("PGPORT")
            if not pg_database: missing_vars.append("PGDATABASE")

            app.logger.error(f"CRITICAL ERROR: Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")
            app.logger.error("These variables must be set in deployment secrets for successful deployment")

            # Log error in deployment mode but continue with SQLite
            if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
                app.logger.error("Continuing with SQLite in deployment mode. This is not recommended for production.")
                
            database_url = "sqlite:///instance/database.db"
            app.logger.warning("Falling back to SQLite database")
else:
    # Development environment
    if not database_url:
        # Try to construct from individual Postgres environment variables
        pg_user = os.environ.get("PGUSER")
        pg_password = os.environ.get("PGPASSWORD")
        pg_host = os.environ.get("PGHOST", "localhost") 
        pg_port = os.environ.get("PGPORT", "5432")
        pg_database = os.environ.get("PGDATABASE")

        if pg_user and pg_password and pg_database:
            # Format database URL correctly for SQLAlchemy
            database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
            app.logger.info(f"Constructed database URL from individual PostgreSQL variables")
        else:
            # Use SQLite for development
            database_url = "sqlite:///instance/database.db"
            app.logger.info("Using SQLite database for development")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Log database configuration (without credentials)
if database_url:
    # Create a safe version of the URL without exposing credentials
    db_log_url = database_url.replace("://", "://***:***@") if "://" in database_url else database_url
    app.logger.info(f"Using database: {db_log_url}")
else:
    app.logger.warning("No database URL configured")


app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size 
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
app.config['DEFAULT_IMAGE'] = 'img/no-image.png'  # Default image to use when one is missing

# Helper function to safely get image paths, falling back to default if image is missing
def get_safe_image_path(image_path):
    """
    Returns a safe image path, checking if the file exists and falling back to default if not.

    Args:
        image_path: Relative path to the image file (usually from database)

    Returns:
        Safe path to use in templates (default image if original is missing)
    """
    if not image_path:
        # No image path provided, use default
        return app.config['DEFAULT_IMAGE']

    # Check if we're in deployment or development
    is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"

    # Construct full path using workspace root to check if file exists
    workspace_root = os.getcwd()
    full_path = os.path.join(workspace_root, 'static', image_path)

    if os.path.isfile(full_path):
        # File exists, return the correct relative path
        return image_path
    else:
        # Log the missing file with detailed information
        app.logger.warning(f"Image file not found: {full_path}")
        app.logger.warning(f"Original path requested: {image_path}")
        app.logger.warning(f"Environment: {'Deployment' if is_deployment else 'Development'}")
        app.logger.warning(f"Working directory: {workspace_root}")
        app.logger.warning(f"Using default image: {app.config['DEFAULT_IMAGE']}")

        # Attempt to create the directory if it doesn't exist
        # This helps when moving between environments
        try:
            directory = os.path.dirname(full_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                app.logger.info(f"Created missing directory: {directory}")
        except Exception as e:
            app.logger.error(f"Error creating directory: {str(e)}")

        return app.config['DEFAULT_IMAGE']

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    try:
        # Get absolute path to PDF directory
        workspace_root = os.getcwd()
        pdf_dir = os.path.join(workspace_root, 'static', 'pdfs')
        file_path = os.path.join(pdf_dir, filename)

        app.logger.info(f"Attempting to serve PDF from: {file_path}")

        if not os.path.exists(file_path):
            app.logger.error(f"PDF not found at path: {file_path}")
            return "PDF not found", 404

        # Get file size for logging
        file_size = os.path.getsize(file_path)
        app.logger.info(f"Found PDF file ({file_size} bytes)")

        download = request.args.get('download', '0') == '1'

        # Use the relative path for send_from_directory
        relative_pdf_dir = os.path.join('static', 'pdfs')

        app.logger.info(f"Serving PDF with download={download}")
        return send_from_directory(
            relative_pdf_dir, 
            filename,
            as_attachment=download,
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Error serving PDF {filename}: {str(e)}")
        # Add stack trace for better debugging
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return f"Error accessing PDF: {str(e)}", 500


db.init_app(app)

logging.basicConfig(level=logging.DEBUG)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('search_home.html')

@app.route('/vmc-admin/', defaults={'path': ''})
@app.route('/vmc-admin/<path:path>')
@login_required
def admin_index(path):
    # Always allow access to the overview page for any logged-in user
    if not path or path == 'overview':
        return redirect(url_for('admin_overview'))

    # For all other admin paths, check if user is an admin
    if not current_user.is_admin:
        flash('You need admin privileges to access this area.', 'danger')
        return redirect(url_for('admin_overview'))

    # For admin users or overview, proceed normally
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/vmc-admin/dashboard')
@login_required
def admin_dashboard():
    category_id = request.args.get('category', type=int)
    query = models.Product.query.order_by(models.Product.created_at.desc())

    if category_id:
        query = query.join(models.Product.categories).filter(models.Category.id == category_id)

    products = query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
    return render_template('product_list.html', products=products, categories=categories, selected_category=category_id)

@app.route('/search')
def search_results():
    query = request.args.get('q', '')
    # Search current products
    products = models.Product.query.filter(
        (models.Product.title.ilike(f'%{query}%'))
        | (models.Product.batch_number.ilike(f'%{query}%'))).all()

    # Search batch history
    batch_history = models.BatchHistory.query.filter(
        models.BatchHistory.batch_number.ilike(f'%{query}%')
    ).all()

    return render_template('search_results.html',
                           products=products,
                           batch_history=batch_history,
                           query=query)


@app.route('/batch/<batch_number>')
def public_product_detail(batch_number):
    # First try to find a current product
    product = models.Product.query.filter_by(batch_number=batch_number).first()
    if product:
        return render_template('public_product_detail.html', 
                             product=product, 
                             is_historical=False)

    # If not found, look for historical record
    history = models.BatchHistory.query.filter_by(batch_number=batch_number).first_or_404()
    return render_template('public_product_detail.html', 
                         product=history.product,
                         batch_history=history,
                         is_historical=True)


@app.route('/vmc-admin/categories')
@login_required
def categories():
    categories = models.Category.query.order_by(models.Category.name).all()
    return render_template('category_list.html', categories=categories)

@app.route('/api/categories', methods=['POST'])
@login_required
@admin_required
def create_category():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400

        category = models.Category()
        category.name = data['name']
        category.description = data.get('description', '')
        db.session.add(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
@admin_required
def update_category(category_id):
    try:
        category = models.Category.query.get_or_404(category_id)
        data = request.get_json()
        category.name = data['name']
        category.description = data.get('description', '')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_category(category_id):
    try:
        category = models.Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/categories/<int:category_id>/sync', methods=['POST'])
@login_required
@admin_required
def sync_category(category_id):
    try:
        from square_category_sync import sync_category_to_square
        category = models.Category.query.get_or_404(category_id)
        result = sync_category_to_square(category)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<int:category_id>/unsync', methods=['POST'])
@login_required
@admin_required
def unsync_category(category_id):
    try:
        category = models.Category.query.get_or_404(category_id)

        # Check if any attached products have Square catalog IDs
        if any(product.square_catalog_id for product in category.products):
            return jsonify({
                'success': False,
                'has_products': True,
                'error': 'Cannot unsync category with Square-synced products'
            }), 400

        from square_category_sync import delete_category_from_square
        result = delete_category_from_square(category)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vmc-admin/products')
@login_required
def products():
    category_id = request.args.get('category', type=int)
    query = models.Product.query.order_by(models.Product.created_at.desc())

    if category_id:
        query = query.join(models.Product.categories).filter(models.Category.id == category_id)

    products = query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
    return render_template('product_list.html', products=products, categories=categories, selected_category=category_id)


def fetch_craftmypdf_templates():
    """Fetch templates from CraftMyPDF API"""
    settings = models.Settings.get_settings()
    try:
        credentials = settings.get_craftmypdf_credentials()
        api_key = credentials['api_key']
    except ValueError:
        app.logger.warning("CraftMyPDF API key not configured")
        return []

    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

    try:
        app.logger.debug("Fetching templates from CraftMyPDF API")
        app.logger.debug(
            "Using API endpoint: https://api.craftmypdf.com/v1/list-templates"
        )

        response = requests.get('https://api.craftmypdf.com/v1/list-templates',
                              headers=headers,
                              params={
                                  'limit': 300,
                                  'offset': 0
                              },
                              timeout=30)

        app.logger.debug(f"API Response Status: {response.status_code}")
        app.logger.debug(f"API Response Headers: {response.headers}")
        app.logger.debug(f"API Response Content: {response.text}")

        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            app.logger.info(f"Successfully fetched {len(templates)} templates")

            # Log template IDs for debugging
            for template in templates:
                app.logger.debug(
                    f"Template ID: {template.get('template_id')}, Name: {template.get('name')}"
                )

            return templates
        else:
            app.logger.error(
                f"Failed to fetch templates. Status: {response.status_code}, Response: {response.text}"
            )
            return []

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request error fetching templates: {str(e)}")
        return []
    except Exception as e:
        app.logger.error(f"Unexpected error fetching templates: {str(e)}")
        return []


@app.route('/vmc-admin/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    templates = models.ProductTemplate.query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
    settings = models.Settings.get_settings()
    has_craftmypdf = bool(settings.craftmypdf_api_key)
    pdf_templates = fetch_craftmypdf_templates()

    if request.method == 'POST':
        title = request.form.get('title')
        attributes = {}

        # Get selected category ID and other fields
        category_id = request.form.get('category_id')
        cost = request.form.get('cost')
        price = request.form.get('price')

        # Process dynamic attributes
        attr_names = request.form.getlist('attr_name[]')
        attr_values = request.form.getlist('attr_value[]')
        attributes = {name: value for name, value in zip(attr_names, attr_values) if name}

        # Generate UPC-A barcode number and SKU
        from utils import generate_upc_barcode, generate_batch_number, generate_sku
        barcode_number = generate_upc_barcode()
        batch_number = request.form.get('batch_number')
        barcode = request.form.get('barcode') # Added to handle manual entry
        manual_sku = request.form.get('sku') # Added to handle manual SKU entry
        if not batch_number:
            batch_number = generate_batch_number()
        sku = manual_sku or generate_sku()  # Use manual entry if available, otherwise auto-generated

        product = models.Product()
        product.title = title
        product.batch_number = batch_number
        product.barcode = barcode or barcode_number # Use manual entry if available, otherwise auto-generated
        product.sku = sku
        product.cost = float(cost) if cost else None
        product.price = float(price) if price else None
        product.craftmypdf_template_id = request.form.get('craftmypdf_template_id')
        product.set_attributes(attributes)

        # Add to database to get product ID
        db.session.add(product)
        db.session.flush()

        # Handle file uploads
        product_image = request.files.get('product_image')
        label_image = request.files.get('label_image')

        if product_image:
            product.product_image = save_image(product_image, product.id, 'product_image')
        if label_image:
            product.label_image = save_image(label_image, product.id, 'label_image')

        # Handle COA PDF upload
        coa_pdf = request.files.get('coa_pdf')
        if coa_pdf and coa_pdf.filename:
            filename = secure_filename(coa_pdf.filename)
            batch_dir = os.path.join('pdfs', product.batch_number)
            filepath = os.path.join(batch_dir, filename)
            os.makedirs(os.path.join('static', batch_dir), exist_ok=True)
            coa_pdf.save(os.path.join('static', filepath))
            product.coa_pdf = filepath

        # Assign category
        if category_id:
            category = models.Category.query.get(category_id)
            if category:
                product.categories = [category]

        db.session.commit()

        # If this is running in production, trigger sync to development
        is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
        if is_deployment:
            try:
                # Import auto sync module
                from auto_sync import trigger_image_sync, trigger_pdf_sync
                # Trigger image sync in background (don't wait for response)
                import threading
                threading.Thread(target=trigger_image_sync, args=(product.id,)).start()
                app.logger.info(f"Triggered image sync for new product ID {product.id}")
                
                # Also trigger PDF sync if needed (for existing PDFs that might have been imported)
                threading.Thread(target=trigger_pdf_sync, args=(product.id,)).start()
                app.logger.info(f"Triggered PDF sync for new product ID {product.id}")
            except Exception as sync_error:
                app.logger.error(f"Error triggering sync: {str(sync_error)}")

        flash('Product created successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('product_create.html',
                           templates=templates,
                           categories=categories,
                           pdf_templates=pdf_templates)


@app.route('/vmc-admin/products/<int:product_id>')
@login_required
def product_detail(product_id):
    product = models.Product.query.get_or_404(product_id)

    # Get previous and next products
    previous_product = models.Product.query.filter(models.Product.id > product_id).order_by(models.Product.id.asc()).first()
    next_product = models.Product.query.filter(models.Product.id < product_id).order_by(models.Product.id.desc()).first()

    # Get all PDFs for this product, including historical ones
    pdfs = models.GeneratedPDF.query.filter(
        models.GeneratedPDF.product_id == product_id
    ).order_by(models.GeneratedPDF.created_at.desc()).all()

    # Debug logging
    app.logger.debug(f"Found {len(pdfs)} PDFs for product {product_id}")
    for pdf in pdfs:
        app.logger.debug(f"PDF ID: {pdf.id}, Filename: {pdf.filename}, Batch History ID: {pdf.batch_history_id}")

    return render_template('product_detail.html', 
                         product=product, 
                         pdfs=pdfs, 
                         previous_product=previous_product,
                         next_product=next_product,
                         BatchHistory=models.BatchHistory)


@app.route('/api/generate_batch', methods=['POST'])
@login_required
def generate_batch():
    return jsonify({'batch_number': generate_batch_number()})


@app.route('/api/generate_pdf/<int:product_id>', methods=['POST'])
@login_required
def generate_pdf(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)

        # Get API key from environment
        settings = models.Settings.get_settings()
        credentials = settings.get_craftmypdf_credentials()
        api_key = credentials['api_key']
        if not api_key:
            app.logger.error("API key not configured")
            return jsonify({'error': 'API key not configured'}), 500

        # Get the JSON structure as generate_json endpoint
        label_data = {
            "batch_lot":
            product.batch_number,
            "sku":
            product.sku,
            "barcode":
            product.barcode,
            "product_name":
            product.title,
            "label_image":
            url_for('static', filename=product.label_image, _external=True)
            if product.label_image else None
        }

        # Add all product attributes
        for key, value in product.get_attributes().items():
            label_data[key.lower().replace(' ', '_')] = value

        # Handle multiple labels structure
        if product.label_qty > 1:
            final_data = {
                "label_data":
                [label_data.copy() for _ in range(product.label_qty)]
            }
        else:
            final_data = label_data

        # Check if we're in development mode - use production URL for generated PDFs
        is_development = os.environ.get("REPLIT_DEPLOYMENT", "0") != "1"
        production_url = "https://viewmycoa.com"

        # Add batch_url to each label's data
        if isinstance(final_data, dict):
            if "label_data" in final_data:
                for label in final_data["label_data"]:
                    # Use production URLs in development, normal URLs in production
                    if is_development:
                        label["batch_url"] = f"{production_url}/batch/{product.batch_number}"
                        if product.label_image and "label_image" in label:
                            label["label_image"] = f"{production_url}/static/{product.label_image}"
                    else:
                        label["batch_url"] = url_for('public_product_detail',
                                                   batch_number=product.batch_number,
                                                   _external=True)
            else:
                if is_development:
                    batch_url = f"{production_url}/batch/{product.batch_number}"
                    if product.label_image and "label_image" in final_data:
                        final_data["label_image"] = f"{production_url}/static/{product.label_image}"
                else:
                    batch_url = url_for('public_product_detail',
                                      batch_number=product.batch_number,
                                      _external=True)

                final_data = {
                    "label_data": [{
                        **final_data,
                        "batch_url": batch_url
                    }]
                }

        api_data = {
            "template_id": product.craftmypdf_template_id,
            "export_type": "json",
            "output_file": f"{product.batch_number}.pdf",
            "expiration": 10,
            "data": json.dumps(final_data)
        }

        # Debug log the final payload
        app.logger.debug(f"Final API Request Data: {api_data}")

        app.logger.debug(f"Final API Request Data: {api_data}")

        app.logger.debug(f"API Request Payload: {api_data}")

        # Debug log the request payload
        app.logger.debug(
            f"Sending request to CraftMyPDF API with payload: {api_data}")

        # Make API call
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

        # Make API request with detailed logging
        response = requests.post('https://api.craftmypdf.com/v1/create',
                                 json=api_data,
                                 headers=headers,
                                 timeout=30)

        # Log full request and response details for debugging
        app.logger.debug(
            "CraftMyPDF API Request URL: https://api.craftmypdf.com/v1/create"
        )
        app.logger.debug(f"CraftMyPDF API Headers: {headers}")
        app.logger.debug(
            f"CraftMyPDF API Response Status: {response.status_code}")
        app.logger.debug(f"CraftMyPDF API Response Content: {response.text}")

        if response.status_code != 200:
            error_msg = f"API Error (Status {response.status_code}): {response.text}"
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), response.status_code

        result = response.json()
        if result.get('status') != 'success':
            error_msg = result.get('message', 'Unknown error')
            app.logger.error(f"API Error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        pdf_url = result.get('file')
        if not pdf_url:
            app.logger.error("No PDF URL in response")
            return jsonify({'error': 'No PDF URL in response'}), 500

        # Create PDF record with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = os.path.join('static', 'pdfs', product.batch_number)
        pdf_filename = f"label_{product.batch_number}_{timestamp}.pdf"
        pdf_filepath = os.path.join(batch_dir, pdf_filename)

        # Ensure batch directory exists
        os.makedirs(batch_dir, exist_ok=True)

        # Download PDF
        pdf_response = requests.get(pdf_url, headers={'Accept': 'application/pdf'})
        if pdf_response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(pdf_filepath), exist_ok=True)

            # Save PDF
            with open(pdf_filepath, 'wb') as f:
                f.write(pdf_response.content)

            # Create PDF record
            pdf = models.GeneratedPDF()
            pdf.product_id = product.id
            pdf.filename = pdf_filename
            pdf.pdf_url = url_for('serve_pdf', filename=os.path.join(product.batch_number, pdf_filename), _external=True)
            db.session.add(pdf)
            db.session.commit()

            # If this is running in production, trigger sync to development
            is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
            if is_deployment:
                try:
                    # Directly run the sync_pdfs.py script with the product ID
                    import threading
                    import subprocess
                    
                    # Use a small delay to ensure the file is fully written before sync
                    def delayed_sync(product_id):
                        import time
                        time.sleep(1)  # Small delay to ensure file is saved completely
                        
                        # Use subprocess to directly run the sync_pdfs.py script
                        try:
                            app.logger.info(f"Running sync_pdfs.py with product ID: {product_id}")
                            result = subprocess.run(
                                [sys.executable, "sync_pdfs.py", str(product_id)],
                                capture_output=True,
                                text=True
                            )
                            if result.returncode == 0:
                                app.logger.info(f"Successfully synced PDF for product ID {product_id}")
                                app.logger.debug(f"Sync output: {result.stdout}")
                            else:
                                app.logger.error(f"PDF sync failed: {result.stderr}")
                        except Exception as run_error:
                            app.logger.error(f"Error running sync_pdfs.py: {str(run_error)}")
                        
                    threading.Thread(target=delayed_sync, args=(product.id,)).start()
                    app.logger.info(f"Scheduled PDF sync for product ID {product.id}")
                except Exception as sync_error:
                    app.logger.error(f"Error triggering PDF sync: {str(sync_error)}")

        return jsonify({'success': True, 'pdf_url':pdf_url})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete_pdf/<int:pdf_id>', methods=['DELETE'])
@login_required
def delete_pdf(pdf_id):
    pdf = models.GeneratedPDF.query.get_or_404(pdf_id)
    try:
        # Get product's batch number
        product = models.Product.query.get(pdf.product_id)
        if product:
            # Delete physical PDF file
            pdf_path = os.path.join('static', 'pdfs', product.batch_number, pdf.filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

                # Check if directory is empty and delete it
                pdf_dir = os.path.dirname(pdf_path)
                if os.path.exists(pdf_dir) and not os.listdir(pdf_dir):
                    os.rmdir(pdf_dir)

        db.session.delete(pdf)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/template/<int:template_id>')
@login_required
def get_template(template_id):
    template = models.ProductTemplate.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'attributes': template.get_attributes()
    })


@app.route('/vmc-admin/templates')
@login_required
def template_list():
    templates = models.ProductTemplate.query.all()
    return render_template('template_list.html', templates=templates)


@app.route('/vmc-admin/template/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_template():
    if request.method == 'POST':
        try:
            template = models.ProductTemplate()
            template.name = request.form['name']

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            attr_values = request.form.getlist('attr_value[]')
            for name, value in zip(attr_names, attr_values):
                if name:  # Only add if name is provided
                    attributes[name] = value
            template.set_attributes(attributes)

            db.session.add(template)
            db.session.commit()

            flash('Template created successfully!', 'success')
            return redirect(url_for('template_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating template: {str(e)}', 'danger')
            return render_template('template_create.html')

    # Handle pre-filled data for duplicating
    prefill_name = request.args.get('name', '')
    prefill_attributes = {}
    if request.args.get('attributes'):
        try:
            prefill_attributes = json.loads(request.args.get('attributes'))
        except json.JSONDecodeError:
            pass

    return render_template('template_create.html', 
                         prefill_name=prefill_name,
                         prefill_attributes=prefill_attributes)

@app.route('/api/square/unsync-all', methods=['POST'])
@login_required
def unsync_all_products():
    """Remove all products from Square"""
    try:
        from square_product_sync import delete_product_from_square
        products = models.Product.query.filter(models.Product.square_catalog_id.isnot(None)).all()

        for product in products:
            result = delete_product_from_square(product)
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'error': f"Error removing product {product.id}: {result['error']}"
                }), 400

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing all products from Square: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/template/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(template_id):
    template = models.ProductTemplate.query.get_or_404(template_id)

    if request.method == 'POST':
        try:
            template.name = request.form['name']

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            attr_values = request.form.getlist('attr_value[]')
            for name, value in zip(attr_names, attr_values):
                if name:  # Only add if name is provided
                    attributes[name] = value
            template.set_attributes(attributes)

            db.session.commit()
            flash('Template updated successfully!', 'success')
            return redirect(url_for('template_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating template: {str(e)}', 'danger')
            return render_template('template_edit.html', template=template)

    return render_template('template_edit.html', template=template)


@app.route('/api/duplicate_template/<int:template_id>', methods=['POST'])
@login_required
@admin_required
def duplicate_template(template_id):
    try:
        original = models.ProductTemplate.query.get_or_404(template_id)
        new_template = models.ProductTemplate()
        new_template.name = f"{original.name} - Copy"
        new_template.set_attributes(original.get_attributes())

        db.session.add(new_template)
        db.session.commit()

        return jsonify({'success': True, 'new_template_id': new_template.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_template/<int:template_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_template(template_id):
    try:
        template = models.ProductTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/vmc-admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = models.Product.query.get_or_404(product_id)
    templates = models.ProductTemplate.query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
    settings = models.Settings.get_settings()
    has_craftmypdf =bool(settings.craftmypdf_api_key)
    pdf_templates = fetch_craftmypdf_templates()

    if request.method == 'POST':
        try:
            product.title = request.form['title']
            product.cost = float(request.form['cost']) if request.form.get('cost') else None
            product.price = float(request.form['price']) if request.form.get('price') else None

            # Handle attributes
            if 'attributes_data' in request.form:
                product.attributes = request.form['attributes_data']
            else:
                # Fall back to processing individual inputs
                attr_names = request.form.getlist('attr_name[]')
                attr_values = request.form.getlist('attr_value[]')
                attrs = {name: value for name, value in zip(attr_names, attr_values) if name}
                product.set_attributes(attrs)
            new_batch_number = request.form['batch_number']
            if new_batch_number != product.batch_number:
                # Create batch history record
                batch_history = models.BatchHistory()
                batch_history.product_id = product.id
                batch_history.batch_number = product.batch_number
                batch_history.set_attributes(product.get_attributes())

                # Move generated PDFs to history
                pdfs = models.GeneratedPDF.query.filter_by(product_id=product.id, batch_history_id=None).all()
                for pdf in pdfs:
                    if pdf.filename.startswith('label_' + product.batch_number):
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        # Create historical version of the label PDF
                        new_filename = f"history_label_{batch_history.batch_number}_{timestamp}.pdf"
                        history_dir = os.path.join('pdfs', batch_history.batch_number)
                        new_filepath = os.path.join(history_dir, new_filename)
                        old_filepath = os.path.join('static', 'pdfs', product.batch_number, pdf.filename)

                        try:
                            if os.path.exists(old_filepath):
                                os.makedirs(os.path.join('static', history_dir), exist_ok=True)
                                import shutil
                                try:
                                    # Copy file first
                                    shutil.copy2(old_filepath, os.path.join('static', new_filepath))
                                    # Only remove original after successful copy
                                    os.remove(old_filepath)

                                    # Update the PDF record
                                    pdf.batch_history_id = batch_history.id
                                    pdf.filename = new_filepath
                                    pdf.pdf_url = url_for('serve_pdf', 
                                                        filename=os.path.join(batch_history.batch_number, new_filename),
                                                        _external=True)
                                    db.session.flush()
                                    app.logger.info(f"Successfully moved PDF {pdf.filename} to batch history")
                                except (shutil.Error, OSError) as e:
                                    app.logger.error(f"Error moving PDF file: {str(e)}")
                                    raise
                        except Exception as e:
                            app.logger.error(f"Error handling PDF file: {str(e)}")
                            db.session.rollback()
                            flash(f"Error preserving PDF files: {str(e)}", 'danger')
                            return render_template('product_edit.html',
                                               product=product,
                                               templates=templates,
                                               categories=categories,
                                               pdf_templates=pdf_templates)

                if product.coa_pdf:
                    # Move COA to history
                    old_coa = product.coa_pdf
                    if old_coa:
                        new_filename = f"history_coa_{batch_history.batch_number}.pdf"
                        history_dir = os.path.join('pdfs', batch_history.batch_number)
                        new_filepath = os.path.join(history_dir, new_filename)
                        try:
                            old_coa_path = os.path.join('static', old_coa)
                            new_coa_path = os.path.join('static', new_filepath)

                            if os.path.exists(old_coa_path) and old_coa_path != new_coa_path:
                                os.makedirs(os.path.join('static', history_dir), exist_ok=True)
                                import shutil
                                try:
                                    shutil.copy2(old_coa_path, new_coa_path)
                                    # Only remove the old file after successful copy
                                    os.remove(old_coa_path)
                                    batch_history.coa_pdf = new_filepath
                                    product.coa_pdf = None
                                    app.logger.info(f"Successfully moved COA file for batch {batch_history.batch_number}")
                                except (shutil.Error, OSError) as e:
                                    app.logger.error(f"Error moving COA file: {str(e)}")
                                    raise
                        except Exception as e:
                            app.logger.error(f"Error handling COA file: {str(e)}")
                            db.session.rollback()
                            flash(f"Error preserving COA file: {str(e)}", 'danger')
                            return render_template('product_edit.html',
                                               product=product,
                                               templates=templates,
                                               categories=categories,
                                               pdf_templates=pdf_templates)

                db.session.add(batch_history)
                product.batch_number = new_batch_number
                product.coa_pdf = None  # Clear current COA
            product.label_qty = int(request.form.get('label_qty', 4))
            product.template_id = request.form.get('template_id', None)
            if request.form.get('craftmypdf_template_id'):
                product.craftmypdf_template_id = request.form['craftmypdf_template_id']

            # Handle category assignment
            category_id = request.form.get('category_id')
            if category_id:
                category = models.Category.query.get(category_id)
                if category:
                    product.categories = [category]
            else:
                product.categories = []  # Clear categories if none selected

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            attr_values = request.form.getlist('attr_value[]')
            for name, value in zip(attr_names, attr_values):
                if name and value:  # Only add if both name and value are provided
                    attributes[name] = value
            product.set_attributes(attributes)
            product.barcode = request.form.get('barcode') # Added to handle manual entry and updates
            product.sku = request.form.get('sku') # Added to handle manual entry and updates for SKU

            # Handle product image with improved path handling
            if 'product_image' in request.files and request.files['product_image'].filename:
                file = request.files['product_image']
                if file and is_valid_image(file):
                    if product.product_image:  # Delete old image if it exists
                        try:
                            # Use absolute path for file operations
                            workspace_root = os.getcwd()
                            old_image_path = os.path.join(workspace_root, 'static', product.product_image)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                                app.logger.info(f"Deleted old product image: {old_image_path}")
                        except OSError as e:
                            app.logger.error(f"Failed to delete old product image: {str(e)}")
                            pass
                    product.product_image = save_image(file, product.id, 'product_image')

            # Handle COA PDF upload with improved path handling
            if 'coa_pdf' in request.files and request.files['coa_pdf'].filename:
                coa_pdf = request.files['coa_pdf']
                if coa_pdf:
                    # Get workspace root for consistent path handling
                    workspace_root = os.getcwd()

                    # Delete old PDF if it exists
                    if product.coa_pdf:
                        try:
                            old_pdf_path = os.path.join(workspace_root, 'static', product.coa_pdf)
                            if os.path.exists(old_pdf_path):
                                os.remove(old_pdf_path)
                                app.logger.info(f"Deleted old PDF: {old_pdf_path}")
                        except OSError as e:
                            app.logger.error(f"Failed to delete old PDF: {str(e)}")
                            pass

                    if coa_pdf.filename:
                        filename = secure_filename(coa_pdf.filename)
                        batch_dir = os.path.join('pdfs', product.batch_number)
                        filepath = os.path.join(batch_dir, filename)

                        # Create directory with absolute path
                        full_dir = os.path.join(workspace_root, 'static', batch_dir)
                        os.makedirs(full_dir, exist_ok=True)
                        app.logger.info(f"Created or verified directory: {full_dir}")

                        # Save file with absolute path
                        full_filepath = os.path.join(workspace_root, 'static', filepath)
                        app.logger.info(f"Saving PDF to: {full_filepath}")
                        coa_pdf.save(full_filepath)

                        # Verify file exists after saving
                        if os.path.exists(full_filepath):
                            app.logger.info(f"Successfully saved PDF: {full_filepath} ({os.path.getsize(full_filepath)} bytes)")
                            product.coa_pdf = filepath
                        else:
                            app.logger.error(f"Failed to save PDF: {full_filepath} does not exist after save operation")

            # Handle label image with improved path handling
            if 'label_image' in request.files and request.files['label_image'].filename:
                file = request.files['label_image']
                if file and is_valid_image(file):
                    if product.label_image:  # Delete old image if it exists
                        try:
                            # Use absolute path for file operations
                            workspace_root = os.getcwd()
                            old_image_path = os.path.join(workspace_root, 'static', product.label_image)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                                app.logger.info(f"Deleted old label image: {old_image_path}")
                        except OSError as e:
                            app.logger.error(f"Failed to delete old label image: {str(e)}")
                            pass
                    product.label_image = save_image(file, product.id, 'label_image')

            db.session.commit()
            
            # If this is running in production, trigger sync to development
            is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
            if is_deployment:
                try:
                    # Import auto sync module
                    from auto_sync import trigger_image_sync, trigger_pdf_sync
                    # Trigger image sync in background
                    import threading
                    threading.Thread(target=trigger_image_sync, args=(product.id,)).start()
                    app.logger.info(f"Triggered image sync for updated product ID {product.id}")
                    
                    # Also trigger PDF sync for updated product
                    threading.Thread(target=trigger_pdf_sync, args=(product.id,)).start()
                    app.logger.info(f"Triggered PDF sync for updated product ID {product.id}")
                except Exception as sync_error:
                    app.logger.error(f"Error triggering sync: {str(sync_error)}")
                    
            flash('Product updated successfully!', 'success')
            show_reminder = '?showSquareReminder=true' if product.square_catalog_id else ''
            return redirect(url_for('product_detail', product_id=product.id) + show_reminder)

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
            return render_template('product_edit.html',
                                   product=product,
                                   templates=templates,
                                   pdf_templates=pdf_templates)

    return render_template('product_edit.html',
                           product=product,
                           templates=templates,
                           categories=categories,
                           pdf_templates=pdf_templates)


@app.context_processor
def inject_settings():
    """Make settings available to all templates."""
    return {
        'settings': models.Settings.get_settings(),
        'get_safe_image_path': get_safe_image_path,
        'is_production': os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
    }

@app.route('/vmc-admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    settings = models.Settings.get_settings()
    products = models.Product.query.all()

    if request.method == 'POST':
        try:
            # Handle Square environment settings
            settings.square_environment = 'production' if request.form.get('square_environment') == 'production' else 'sandbox'
            settings.square_sandbox_access_token = request.form.get('square_sandbox_access_token')
            settings.square_sandbox_location_id = request.form.get('square_sandbox_location_id')
            settings.square_production_access_token = request.form.get('square_production_access_token')
            settings.square_production_location_id = request.form.get('square_production_location_id')

            # Handle development settings
            settings.show_square_id_controls = bool(request.form.get('show_square_id'))
            settings.show_square_image_id_controls = bool(request.form.get('show_square_image_id'))

            # Update CraftMyPDF settings
            settings.craftmypdf_api_key = request.form.get('craftmypdf_api_key')

            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')

    return render_template('settings.html', settings=settings, products=products)

@app.route('/api/delete_batch_history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_batch_history(history_id):
    try:
        history = models.BatchHistory.query.get_or_404(history_id)
        workspace_root = os.getcwd()

        # Delete the entire batch directory with absolute path
        batch_dir_rel = os.path.join('pdfs', history.batch_number)
        batch_dir = os.path.join(workspace_root, 'static', batch_dir_rel)
        if os.path.exists(batch_dir):
            import shutil
            app.logger.info(f"Deleting batch directory: {batch_dir}")
            shutil.rmtree(batch_dir)
            app.logger.info(f"Successfully deleted batch directory")

        # Delete historical COA if exists and it's not in the batch directory
        if history.coa_pdf:
            coa_path = os.path.join(workspace_root, 'static', history.coa_pdf)
            if os.path.exists(coa_path) and history.coa_pdf.find(batch_dir_rel) == -1:
                app.logger.info(f"Deleting historical COA file: {coa_path}")
                os.remove(coa_path)
                app.logger.info(f"Successfully deleted COA file")

        # Delete PDF records
        pdfs = models.GeneratedPDF.query.filter_by(
            batch_history_id=history.id
        ).all()
        app.logger.info(f"Deleting {len(pdfs)} PDF records from database")
        for pdf in pdfs:
            db.session.delete(pdf)

        db.session.delete(history)
        db.session.commit()
        app.logger.info(f"Successfully deleted batch history ID {history_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting batch history: {str(e)}")
        # Add stack trace for better debugging
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_coa/<int:product_id>', methods=['DELETE'])
@login_required
def delete_coa(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)
        if product.coa_pdf:
            # Delete physical file with absolute path
            workspace_root = os.getcwd()
            file_path = os.path.join(workspace_root, 'static', product.coa_pdf)
            if os.path.exists(file_path):
                app.logger.info(f"Deleting COA file: {file_path}")
                os.remove(file_path)
                app.logger.info(f"Successfully deleted COA file")
            else:
                app.logger.warning(f"COA file not found for deletion: {file_path}")

            # Clear database reference
            product.coa_pdf = None
            db.session.commit()
            app.logger.info(f"Successfully cleared COA reference for product ID {product_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting COA: {str(e)}")
        # Add stack trace for better debugging
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/duplicate_product/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def duplicate_product(product_id):
    try:
        from utils import generate_batch_number, generate_sku, generate_upc_barcode
        original = models.Product.query.get_or_404(product_id)

        # Create new product with copied attributes
        new_product = models.Product()
        new_product.title = f"{original.title} - Copy"
        new_product.batch_number = generate_batch_number()
        new_product.sku = generate_sku()
        new_product.barcode = generate_upc_barcode()
        new_product.cost = original.cost
        new_product.price = original.price
        new_product.set_attributes(original.get_attributes())

        new_product.template_id = original.template_id
        new_product.craftmypdf_template_id = original.craftmypdf_template_id
        new_product.label_qty = original.label_qty

        # Handle categories properly
        if len(original.categories) > 0:
            new_product.categories = list(original.categories)

        db.session.add(new_product)
        db.session.flush()  # Get the new product ID

        # Create product directory after we have the ID
        product_dir = os.path.join('static', 'uploads', str(new_product.id))
        os.makedirs(product_dir, exist_ok=True)

        # Handle product image duplication
        if original.product_image:
            original_path = os.path.join('static', original.product_image)
            if os.path.exists(original_path):
                ext = os.path.splitext(original.product_image)[1]
                new_filename = f'product_image_{new_product.id}{ext}'
                new_path = os.path.join(product_dir, new_filename)
                import shutil
                shutil.copy2(original_path, new_path)
                new_product.product_image = os.path.join('uploads', str(new_product.id), new_filename)

        # Handle label image duplication
        if original.label_image:
            original_path = os.path.join('static', original.label_image)
            if os.path.exists(original_path):
                ext = os.path.splitext(original.label_image)[1]
                new_filename = f'label_image_{new_product.id}{ext}'
                new_path = os.path.join(product_dir, new_filename)
                import shutil
                shutil.copy2(original_path, new_path)
                new_product.label_image = os.path.join('uploads', str(new_product.id), new_filename)
        new_product.craftmypdf_template_id = original.craftmypdf_template_id
        new_product.label_qty = original.label_qty

        # Handle categories properly
        if len(original.categories) > 0:
            new_product.categories = list(original.categories)

        db.session.add(new_product)
        db.session.flush()  # Flush to get the new ID without committing
        db.session.commit()

        app.logger.info(f"Successfully duplicated product {product_id} to {new_product.id}")
        return jsonify({'success': True, 'new_product_id': new_product.id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error duplicating product {product_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/delete_product/<int:product_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_product(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)
        batch_number = product.batch_number

        # Use absolute paths for file operations
        workspace_root = os.getcwd()
        product_dir_rel = os.path.join('static', 'uploads', str(product.id))
        pdf_dir_rel = os.path.join('static', 'pdfs', batch_number)
        product_dir = os.path.join(workspace_root, product_dir_rel)
        pdf_dir = os.path.join(workspace_root, pdf_dir_rel)

        # If product has Square ID, remove from Square first
        if product.square_catalog_id:
            from square_product_sync import delete_product_from_square
            result = delete_product_from_square(product)
            if 'error' in result:
                return jsonify({'error': f"Failed to remove from Square: {result['error']}"}), 500

        with db.session.begin_nested():
            # Clear categories using SQL
            db.session.execute(
                product_categories.delete().where(product_categories.c.product_id == product_id)
            )

            # Delete batch histories and PDFs
            models.BatchHistory.query.filter_by(product_id=product_id).delete()
            models.GeneratedPDF.query.filter_by(product_id=product_id).delete()

            # Delete the product
            db.session.delete(product)

        # Commit the transaction
        db.session.commit()
        app.logger.info(f"Successfully deleted product ID {product_id} from database")

        # Clean up files after successful database operations
        if os.path.exists(pdf_dir):
            try:
                import shutil
                app.logger.info(f"Deleting PDF directory: {pdf_dir}")
                shutil.rmtree(pdf_dir)
                app.logger.info(f"Successfully deleted PDF directory")
            except OSError as e:
                app.logger.warning(f"Error deleting PDF directory: {e}")

        if os.path.exists(product_dir):
            try:
                import shutil
                app.logger.info(f"Deleting product directory: {product_dir}")
                shutil.rmtree(product_dir)
                app.logger.info(f"Successfully deleted product directory")
            except OSError as e:
                app.logger.warning(f"Error deleting product directory: {e}")

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting product: {e}")
        # Add stack trace for better debugging
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_json/<int:product_id>')
@login_required
def generate_json(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)
        settings = models.Settings.get_settings()

        # Check if we're in development mode - use production URL for generated PDFs
        is_development = os.environ.get("REPLIT_DEPLOYMENT", "0") != "1"
        production_url = "https://viewmycoa.com"

        # Create base label data structure
        label_data = {
            "batch_lot": product.batch_number,
            "sku": product.sku,
            "barcode": product.barcode,
            "product_name": product.title,
        }

        # Use production URLs when in development, or normal URLs in production
        if is_development and product.label_image:
            # Use production URL for images in development
            label_data["label_image"] = f"{production_url}/static/{product.label_image}"
            label_data["batch_url"] = f"{production_url}/batch/{product.batch_number}"
        else:
            # In production, use the normal URL generation
            label_data["label_image"] = url_for('static', 
                                              filename=product.label_image, 
                                              _external=True) if product.label_image else None
            label_data["batch_url"] = url_for('public_product_detail',
                                            batch_number=product.batch_number,
                                            _external=True)

        # Add all product attributes
        for key, value in product.get_attributes().items():
            label_data[key.lower().replace(' ', '_')] = value

        # Structure the response based on label quantity
        if product.label_qty > 1:
            response_data = {
                "label_data":
                [label_data.copy() for _ in range(product.label_qty)]
            }
        else:
            response_data = label_data

        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error generating JSON: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/square/sync/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def sync_single_product(product_id):
    """Sync a single product to Square"""
    try:
        from square_product_sync import sync_product_to_square
        product = models.Product.query.get_or_404(product_id)
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

def save_image(file, product_id, image_type):
    """
    Save an uploaded image file for a product with improved cross-environment compatibility.

    Args:
        file: The uploaded file object
        product_id: The product ID to associate with this image
        image_type: Type of image (product_image, label_image, etc.)

    Returns:
        The relative path to the saved image
    """
    try:
        # Check if we're in deployment or development - useful for logging
        is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
        app.logger.info(f"Saving image in {'deployment' if is_deployment else 'development'} environment")

        # If this is running in production, trigger sync to development
        if is_deployment:
            try:
                # Import auto sync module
                from auto_sync import trigger_image_sync
                # Trigger image sync in background (don't wait for response)
                import threading
                threading.Thread(target=trigger_image_sync, args=(product_id,)).start()
                app.logger.info(f"Triggered image sync for product ID {product_id}")
            except Exception as sync_error:
                app.logger.error(f"Error triggering image sync: {str(sync_error)}")

        # Use absolute path with workspace root for consistency
        workspace_root = os.getcwd()

        # Create product-specific directory 
        product_dir = os.path.join('uploads', str(product_id))
        relative_dir = os.path.join('static', product_dir)
        full_dir = os.path.join(workspace_root, relative_dir)

        # Make sure directory exists
        try:
            os.makedirs(full_dir, exist_ok=True)
            app.logger.info(f"Created or verified directory: {full_dir}")
        except Exception as dir_error:
            app.logger.error(f"Failed to create directory {full_dir}: {str(dir_error)}")
            # Try to continue anyway

        # Get file extension with validation
        orig_filename = secure_filename(file.filename)
        if not orig_filename:
            app.logger.warning(f"Invalid filename for {image_type}, using default extension")
            ext = '.png'
        else:
            ext = os.path.splitext(orig_filename)[1].lower()
            if not ext:
                ext = '.png'  # Default to png if no extension

            # Ensure we have a valid extension for web images
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if ext.lower() not in valid_extensions:
                ext = '.png'  # Default to PNG for unsupported formats

        # IMPORTANT CHANGE: Use a completely deterministic filename that will be the same
        # in both production and development for the same product
        # Remove any timestamp or random components that would make filenames differ
        filename = f"{image_type}_{product_id}{ext}"
        filepath = os.path.join(product_dir, filename)
        full_filepath = os.path.join(workspace_root, 'static', filepath)

        # Process and save image
        img = Image.open(file)

        # Resize to reasonable dimensions to save space and ensure consistency
        img.thumbnail((800, 800))  # Consistent size across environments

        # Ensure the image is in a web-friendly format
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')

        # Log before saving
        app.logger.info(f"Saving image to: {full_filepath}")

        # Save with explicit format
        format_type = 'PNG' if ext.lower() == '.png' else 'JPEG'
        img.save(full_filepath, format=format_type, quality=85)  # Consistent quality

        # Verify file exists after saving
        if os.path.exists(full_filepath):
            app.logger.info(f"Successfully saved image: {full_filepath} ({os.path.getsize(full_filepath)} bytes)")
        else:
            app.logger.error(f"Failed to save image: {full_filepath} does not exist after save operation")
            return 'img/no-image.png'

        # Return path relative to static directory for proper URL generation
        return filepath
    except Exception as e:
        app.logger.error(f"Error saving image: {str(e)}")
        import traceback
        app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return 'img/no-image.png'

@app.route('/api/square/clear-id/<int:product_id>', methods=['POST']) 
@login_required
@admin_required
def clear_square_id(product_id):
    """Clear Square catalog ID from product"""
    try:
        product = models.Product.query.get_or_404(product_id)
        product.square_catalog_id = None
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/square/unsync/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def unsync_product(product_id):
    """Remove product from Square"""
    try:
        from square_product_sync import delete_product_from_square
        product = models.Product.query.get_or_404(product_id)
        result = delete_product_from_square(product)

        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error unsyncing product from Square: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@app.route('/api/square/clear-image-id/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def clear_square_image_id(product_id):
    """Clear Square image ID from product"""
    try:
        product = models.Product.query.get_or_404(product_id)
        product.square_image_id = None
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/images', methods=['POST'])
def sync_images_api():
    """
    API endpoint to sync images for specific product IDs
    Expects a JSON payload with 'product_ids' as a list of ints
    """
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])

        if not product_ids:
            return jsonify({'error': 'No product IDs provided'}), 400

        app.logger.info(f"API request to sync images for product IDs: {product_ids}")

        # Import here to avoid circular import
        from sync_images import sync_product_images

        # Execute sync for specified products only
        sync_product_images(product_ids)

        return jsonify({'success': True, 'message': f'Synced images for product IDs: {product_ids}'})

    except Exception as e:
        app.logger.error(f"Error in sync images API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/pdfs', methods=['POST'])
def sync_pdfs_api():
    """
    API endpoint to sync PDFs for specific product IDs
    Expects a JSON payload with 'product_ids' as a list of ints
    """
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])

        if not product_ids:
            return jsonify({'error': 'No product IDs provided'}), 400

        app.logger.info(f"API request to sync PDFs for product IDs: {product_ids}")

        # Import here to avoid circular import
        from sync_pdfs import sync_product_pdfs

        # Execute sync for specified products only
        sync_product_pdfs(product_ids)

        return jsonify({'success': True, 'message': f'Synced PDFs for product IDs: {product_ids}'})

    except Exception as e:
        app.logger.error(f"Error in sync PDFs API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """
    Health check endpoint for deployment
    Returns 200 OK if the application is running
    """
    app.logger.info("Health check request received")
    return 'OK', 200

if __name__ == "__main__":
    # Use port 3000 for both development and production to ensure consistency
    port = int(os.environ.get("PORT", 3000))
    app.logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port)