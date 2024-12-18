import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.utils import secure_filename
import string
import random
import requests
import json
from PIL import Image
import datetime

import utils


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


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



@app.route('/products')
def products():
    products = models.Product.query.all()
    return render_template('product_list.html', products=products)


def fetch_craftmypdf_templates():
    """Fetch templates from CraftMyPDF API"""
    api_key = os.environ.get('CRAFTMYPDF_API_KEY')
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


@app.route('/product/new', methods=['GET', 'POST'])
def create_product():
    templates = models.ProductTemplate.query.all()
    pdf_templates = fetch_craftmypdf_templates()

    if request.method == 'POST':
        title = request.form.get('title')
        attributes = {}

        # Process dynamic attributes
        attr_names = request.form.getlist('attr_name[]')
        attr_values = request.form.getlist('attr_value[]')
        attributes = dict(zip(attr_names, attr_values))

        # Handle file uploads
        product_image = request.files.get('product_image')
        label_image = request.files.get('label_image')

        # Generate UPC-A barcode number
        barcode_number = utils.generate_upc_barcode()
        batch_number = generate_batch_number()
        sku = utils.generate_sku()  # Generate unique SKU

        product = models.Product()
        product.title = title
        product.batch_number = batch_number
        product.barcode = barcode_number
        product.sku = sku
        product.craftmypdf_template_id = request.form.get('craftmypdf_template_id')
        product.set_attributes(attributes)

        if product_image:
            product.product_image = save_image(product_image)
        if label_image:
            product.label_image = save_image(label_image)

        # Handle COA PDF upload
        coa_pdf = request.files.get('coa_pdf')
        if coa_pdf and coa_pdf.filename:
            filename = secure_filename(coa_pdf.filename)
            filepath = os.path.join('pdfs', filename)
            os.makedirs(os.path.join('static', 'pdfs'), exist_ok=True)
            coa_pdf.save(os.path.join('static', filepath))
            product.coa_pdf = filepath

        db.session.add(product)
        db.session.commit()

        flash('Product created successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('product_create.html',
                           templates=templates,
                           pdf_templates=pdf_templates)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = models.Product.query.get_or_404(product_id)
    pdfs = models.GeneratedPDF.query.filter_by(product_id=product_id).order_by(
        models.GeneratedPDF.created_at.desc()).all()
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
        api_key = os.environ.get('CRAFTMYPDF_API_KEY')
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
        pdf_filename = f"label_{product.batch_number}_{timestamp}.pdf"
        pdf_filepath = os.path.join('static', 'pdfs', pdf_filename)

        # Ensure pdfs directory exists
        os.makedirs(os.path.join('static', 'pdfs'), exist_ok=True)

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
            pdf.pdf_url = url_for('serve_pdf', filename=pdf_filename, _external=True)
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
        # Delete physical PDF file
        pdf_path = os.path.join('static', 'pdfs', pdf.filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
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


@app.route('/templates')
def template_list():
    templates = models.ProductTemplate.query.all()
    return render_template('template_list.html', templates=templates)


@app.route('/template/new', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        try:
            template = models.ProductTemplate()
            template.name = request.form['name']

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            for name in attr_names:
                if name:  # Only add if name is provided
                    attributes[
                        name] = ""  # Empty value as it's just a template
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


@app.route('/template/<int:template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    template = models.ProductTemplate.query.get_or_404(template_id)

    if request.method == 'POST':
        try:
            template.name = request.form['name']

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            for name in attr_names:
                if name:  # Only add if name is provided
                    attributes[
                        name] = ""  # Empty value as it's just a template
            template.set_attributes(attributes)

            db.session.commit()
            flash('Template updated successfully!', 'success')
            return redirect(url_for('template_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating template: {str(e)}', 'danger')
            return render_template('template_edit.html', template=template)

    return render_template('template_edit.html', template=template)


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


@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = models.Product.query.get_or_404(product_id)
    templates = models.ProductTemplate.query.all()
    pdf_templates = fetch_craftmypdf_templates()

    if request.method == 'POST':
        try:
            product.title = request.form['title']
            new_batch_number = request.form['batch_number']
            if new_batch_number != product.batch_number:
                # Create batch history record
                batch_history = models.BatchHistory()
                batch_history.product_id = product.id
                batch_history.batch_number = product.batch_number
                batch_history.set_attributes(product.get_attributes())
                
                # Move generated PDFs to history
                pdfs = models.GeneratedPDF.query.filter_by(product_id=product.id).all()
                for pdf in pdfs:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    if pdf.filename.startswith('label_' + product.batch_number):
                        # Create historical version of the label PDF
                        new_filename = f"history_label_{batch_history.batch_number}_{timestamp}.pdf"
                        new_filepath = os.path.join('static', 'pdfs', new_filename)
                        old_filepath = os.path.join('static', 'pdfs', pdf.filename)
                        
                        try:
                            if os.path.exists(old_filepath):
                                import shutil
                                shutil.copy2(old_filepath, new_filepath)
                                os.remove(old_filepath)  # Remove original file
                                # Create new PDF record for historical label
                                # Delete the old PDF record first
                                db.session.delete(pdf)
                                
                                # Create historical PDF record with batch history reference
                                historical_pdf = models.GeneratedPDF()
                                historical_pdf.product_id = product.id
                                historical_pdf.batch_history_id = batch_history.id
                                historical_pdf.filename = new_filename
                                historical_pdf.pdf_url = url_for('serve_pdf', filename=new_filename, _external=True)
                                db.session.add(historical_pdf)
                        except Exception as e:
                            app.logger.error(f"Error moving PDF file: {str(e)}")

                if product.coa_pdf:
                    # Move COA to history
                    old_coa = product.coa_pdf
                    if old_coa:
                        new_filename = f"history_{os.path.basename(old_coa)}"
                        new_filepath = os.path.join('pdfs', new_filename)
                        try:
                            if os.path.exists(os.path.join('static', old_coa)):
                                os.makedirs(os.path.join('static', 'pdfs'), exist_ok=True)
                                import shutil
                                shutil.move(
                                    os.path.join('static', old_coa),
                                    os.path.join('static', new_filepath)
                                )
                                batch_history.coa_pdf = new_filepath
                                product.coa_pdf = None
                        except Exception as e:
                            app.logger.error(f"Error moving COA file: {str(e)}")

                db.session.add(batch_history)
                product.batch_number = new_batch_number
                product.coa_pdf = None  # Clear current COA
            product.label_qty = int(request.form.get('label_qty', 4))
            product.template_id = request.form.get('template_id', None)
            if request.form.get('craftmypdf_template_id'):
                product.craftmypdf_template_id = request.form[
                    'craftmypdf_template_id']

            # Handle attributes
            attributes = {}
            attr_names = request.form.getlist('attr_name[]')
            attr_values = request.form.getlist('attr_value[]')
            for name, value in zip(attr_names, attr_values):
                if name and value:  # Only add if both name and value are provided
                    attributes[name] = value
            product.set_attributes(attributes)

            # Handle product image
            if 'product_image' in request.files and request.files[
                    'product_image'].filename:
                file = request.files['product_image']
                if file and utils.is_valid_image(file):
                    if product.product_image:  # Delete old image if it exists
                        try:
                            os.remove(
                                os.path.join('static', product.product_image))
                        except OSError:
                            pass
                    filename = utils.clean_filename(file.filename)
                    filepath = os.path.join('uploads', filename)
                    processed_image = utils.process_image(file)
                    with open(os.path.join('static', filepath), 'wb') as f:
                        f.write(processed_image.getvalue())
                    product.product_image = filepath

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
                        filepath = os.path.join('pdfs', filename)
                        os.makedirs(os.path.join('static', 'pdfs'), exist_ok=True)
                        coa_pdf.save(os.path.join('static', filepath))
                        product.coa_pdf = filepath

            # Handle label image
            if 'label_image' in request.files and request.files[
                    'label_image'].filename:
                file = request.files['label_image']
                if file and utils.is_valid_image(file):
                    if product.label_image:  # Delete old image if it exists
                        try:
                            os.remove(
                                os.path.join('static', product.label_image))
                        except OSError:
                            pass
                    filename = utils.clean_filename(file.filename)
                    filepath = os.path.join('uploads', filename)
                    processed_image = utils.process_image(file)
                    with open(os.path.join('static', filepath), 'wb') as f:
                        f.write(processed_image.getvalue())
                    product.label_image = filepath

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('product_detail', product_id=product.id))

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
                           pdf_templates=pdf_templates)


@app.route('/api/delete_batch_history/<int:history_id>', methods=['DELETE'])
def delete_batch_history(history_id):
    try:
        history = models.BatchHistory.query.get_or_404(history_id)
        # Delete historical COA if exists
        if history.coa_pdf:
            coa_path = os.path.join('static', history.coa_pdf)
            if os.path.exists(coa_path):
                os.remove(coa_path)
                
        # Delete historical label PDFs
        pdfs = models.GeneratedPDF.query.filter_by(product_id=history.product_id).all()
        for pdf in pdfs:
            if pdf.filename.startswith(f"history_{history.batch_number}"):
                pdf_path = os.path.join('static', 'pdfs', pdf.filename)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                db.session.delete(pdf)
                
        db.session.delete(history)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
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

@app.route('/api/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = models.Product.query.get_or_404(product_id)

        # Delete all associated PDFs
        pdfs = models.GeneratedPDF.query.filter_by(
            product_id=product_id).order_by(
                models.GeneratedPDF.created_at.desc()).all()
        for pdf in pdfs:
            try:
                pdf_path = os.path.join('static', 'pdfs', pdf.filename)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except OSError as e:
                logging.error(f"Error deleting PDF file: {e}")

        # Delete product images
        for image_field in ['product_image', 'label_image']:
            image_path = getattr(product, image_field)
            if image_path:
                try:
                    full_path = os.path.join('static', image_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except OSError as e:
                    logging.error(f"Error deleting {image_field}: {e}")

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


def generate_batch_number():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))


def save_image(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Process and save image
    img = Image.open(file)
    img.thumbnail((800, 800))  # Resize if needed
    img.save(filepath)

    # Return relative path from static folder
    return filepath.replace('static/', '', 1)