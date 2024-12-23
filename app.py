import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import logging
from werkzeug.utils import secure_filename
import requests
import json
from PIL import Image
import datetime
from flask_migrate import Migrate
from utils import generate_batch_number, is_valid_image
from models import db, product_categories, Settings

app = Flask(__name__)

# Basic configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

# Initialize migrations after database setup
migrate = Migrate(app, db)

# Create tables and get settings
with app.app_context():
    db.create_all()
    settings = Settings.get_settings()
    app.secret_key = settings.get_secret_key()

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
        pdf_dir = os.path.join('static', 'pdfs')
        file_path = os.path.join(pdf_dir, filename)

        if not os.path.exists(file_path):
            app.logger.error(f"PDF not found at path: {file_path}")
            return "PDF not found", 404

        download = request.args.get('download', '0') == '1'

        return send_from_directory(
            pdf_dir,
            filename,
            as_attachment=download,
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Error serving PDF {filename}: {str(e)}")
        return f"Error accessing PDF: {str(e)}", 500


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
def admin_index(path):
    if not path:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/vmc-admin/dashboard')
def admin_dashboard():
    products = models.Product.query.all()
    return render_template('product_list.html', products=products)

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
def categories():
    categories = models.Category.query.order_by(models.Category.name).all()
    return render_template('category_list.html', categories=categories)

@app.route('/api/categories', methods=['POST'])
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
def products():
    products = models.Product.query.order_by(models.Product.created_at.desc()).all()
    return render_template('product_list.html', products=products)


def fetch_craftmypdf_templates():
    """Fetch templates from CraftMyPDF API"""
    settings = Settings.get_settings()
    credentials = settings.get_craftmypdf_credentials()
    api_key = credentials['api_key']

    if not api_key:
        app.logger.error("CraftMyPDF API key not configured")
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
def create_product():
    templates = models.ProductTemplate.query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
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
        attributes = dict(zip(attr_names, attr_values))

        # Generate UPC-A barcode number and SKU
        from utils import generate_upc_barcode, generate_batch_number, generate_sku
        barcode_number = generate_upc_barcode()
        batch_number = request.form.get('batch_number')
        if not batch_number:
            batch_number = generate_batch_number()
        sku = generate_sku()  # Generate unique SKU

        product = models.Product()
        product.title = title
        product.batch_number = batch_number
        product.barcode = barcode_number
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

        db.session.add(product)
        db.session.commit()

        flash('Product created successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('product_create.html',
                           templates=templates,
                           categories=categories,
                           pdf_templates=pdf_templates)


@app.route('/vmc-admin/products/<int:product_id>')
def product_detail(product_id):
    product = models.Product.query.get_or_404(product_id)
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
                         BatchHistory=models.BatchHistory)


@app.route('/api/generate_batch', methods=['POST'])
def generate_batch():
    return jsonify({'batch_number': generate_batch_number()})


@app.route('/api/generate_pdf/<int:product_id>', methods=['POST'])
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

        # Add batch_url to each label's data
        if isinstance(final_data, dict):
            if "label_data" in final_data:
                for label in final_data["label_data"]:
                    label["batch_url"] = url_for('public_product_detail',
                                                 batch_number=product.batch_number,
                                                 _external=True)
            else:
                final_data = {
                    "label_data": [{
                        **final_data,
                        "batch_url": url_for('public_product_detail',
                                             batch_number=product.batch_number,
                                             _external=True)
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

        return jsonify({'success': True, 'pdf_url': pdf_url})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"API request error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete_pdf/<int:pdf_id>', methods=['DELETE'])
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
def get_template(template_id):
    template = models.ProductTemplate.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'attributes': template.get_attributes()
    })


@app.route('/vmc-admin/templates')
def template_list():
    templates = models.ProductTemplate.query.all()
    return render_template('template_list.html', templates=templates)


@app.route('/vmc-admin/template/new', methods=['GET', 'POST'])
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

    return render_template('template_create.html')

@app.route('/api/square/unsync-all', methods=['POST'])
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
def edit_product(product_id):
    product = models.Product.query.get_or_404(product_id)
    templates = models.ProductTemplate.query.all()
    categories = models.Category.query.order_by(models.Category.name).all()
    pdf_templates = fetch_craftmypdf_templates()

    if request.method == 'POST':
        try:
            product.title = request.form['title']
            product.cost = float(request.form['cost']) if request.form.get('cost') else None
            product.price = float(request.form['price']) if request.form.get('price') else None
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

            # Handle product image
            # Handle product image
            if 'product_image' in request.files and request.files['product_image'].filename:
                file = request.files['product_image']
                if file and is_valid_image(file):
                    if product.product_image:  # Delete old image if it exists
                        try:
                            os.remove(os.path.join('static', product.product_image))
                        except OSError:
                            pass
                    product.product_image = save_image(file, product.id, 'product_image')

            # Handle COA PDF upload
            if 'coa_pdf' in request.files and request.files['coa_pdf'].filename:
                coa_pdf = request.files['coa_pdf']
                if coa_pdf:
                    if product.coa_pdf:  # Delete old PDF if it exists
                        try:
                            os.remove(os.path.join('static', product.coa_pdf))
                        except OSError:
                            pass
                    if coa_pdf.filename:
                        filename = secure_filename(coa_pdf.filename)
                        batch_dir = os.path.join('pdfs', product.batch_number)
                        filepath = os.path.join(batch_dir, filename)
                        os.makedirs(os.path.join('static', batch_dir), exist_ok=True)
                        coa_pdf.save(os.path.join('static', filepath))
                        product.coa_pdf = filepath

            # Handle label image
            if 'label_image' in request.files and request.files['label_image'].filename:
                file = request.files['label_image']
                if file and is_valid_image(file):
                    if product.label_image:  # Delete old image if it exists
                        try:
                            os.remove(os.path.join('static', product.label_image))
                        except OSError:
                            pass
                    product.label_image = save_image(file, product.id, 'label_image')

            db.session.commit()
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
    return {'settings': models.Settings.get_settings()}

@app.route('/vmc-admin/settings', methods=['GET', 'POST'])
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
def delete_batch_history(history_id):
    try:
        history = models.BatchHistory.query.get_or_404(history_id)

        # Delete the entire batch directory
        batch_dir = os.path.join('static', 'pdfs', history.batch_number)
        if os.path.exists(batch_dir):
            import shutil
            shutil.rmtree(batch_dir)

        # Delete historical COA if exists and it's not in the batch directory
        if history.coa_pdf:
            coa_path = os.path.join('static', history.coa_pdf)
            if os.path.exists(coa_path) and not coa_path.startswith(batch_dir):
                os.remove(coa_path)

        # Delete PDF records
        pdfs = models.GeneratedPDF.query.filter_by(
            batch_history_id=history.id
        ).all()
        for pdf in pdfs:
            db.session.delete(pdf)

        db.session.delete(history)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting batch history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_coa/<int:product_id>', methods=['DELETE'])
def delete_coa(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)
        if product.coa_pdf:
            # Delete physical file
            file_path = os.path.join('static', product.coa_pdf)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Clear database reference
            product.coa_pdf = None
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/duplicate_product/<int:product_id>', methods=['POST'])
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
def delete_product(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)
        batch_number = product.batch_number

        # Clear categories using SQL to avoid constraint issues
        db.session.execute(
            product_categories.delete().where(product_categories.c.product_id == product_id)
        )
        db.session.flush()

        # Delete batch history records
        batch_histories = models.BatchHistory.query.filter_by(product_id=product_id).all()
        for history in batch_histories:
            db.session.delete(history)

        # Delete PDFs and their directory
        pdfs = models.GeneratedPDF.query.filter_by(product_id=product_id).all()
        for pdf in pdfs:
            db.session.delete(pdf)

        # Delete PDF directory if it exists
        pdf_dir = os.path.join('static', 'pdfs', batch_number)
        if os.path.exists(pdf_dir):
            try:
                import shutil
                shutil.rmtree(pdf_dir)
            except OSError as e:
                logging.error(f"Error deleting PDF directory: {e}")

        # Delete product directory with all images
        product_dir = os.path.join('static', 'uploads', str(product.id))
        if os.path.exists(product_dir):
            try:
                import shutil
                shutil.rmtree(product_dir)
            except OSError as e:
                logging.error(f"Error deleting product directory: {e}")

        # Delete the product and commit all changes
        db.session.delete(product)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting product: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_json/<int:product_id>')
def generate_json(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)

        # Create base label data structure
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
            if product.label_image else None,
            "batch_url":
            url_for('public_product_detail',
                    batch_number=product.batch_number,
                    _external=True)
        }

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
    # Create product-specific directory
    product_dir = os.path.join('uploads', str(product_id))
    full_dir = os.path.join('static', product_dir)
    os.makedirs(full_dir, exist_ok=True)

    # Get file extension
    ext = os.path.splitext(secure_filename(file.filename))[1]

    # Create filename based on product_id and type
    filename = f"{image_type}_{product_id}{ext}"
    filepath = os.path.join(product_dir, filename)

    # Process and save image
    img = Image.open(file)
    img.thumbnail((800, 800))  # Resize if needed
    img.save(os.path.join('static', filepath))

    return filepath

@app.route('/api/square/clear-id/<int:product_id>', methods=['POST'])
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