import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.utils import secure_filename
import string
import random
import requests
from PIL import Image
import io
import base64

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
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

logging.basicConfig(level=logging.DEBUG)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    products = models.Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/product/new', methods=['GET', 'POST'])
def create_product():
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

        product = models.Product(
            title=title,
            batch_number=generate_batch_number(),
        )
        product.set_attributes(attributes)

        if product_image:
            product.product_image = save_image(product_image)
        if label_image:
            product.label_image = save_image(label_image)

        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('product_create.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = models.Product.query.get_or_404(product_id)
    pdfs = models.GeneratedPDF.query.filter_by(product_id=product_id).all()
    return render_template('product_detail.html', product=product, pdfs=pdfs)

@app.route('/api/generate_batch', methods=['POST'])
def generate_batch():
    return jsonify({'batch_number': generate_batch_number()})

@app.route('/api/generate_pdf/<int:product_id>', methods=['POST'])
def generate_pdf(product_id):
    product = models.Product.query.get_or_404(product_id)
    
    # Prepare data for CraftMyPDF API
    pdf_data = {
        'title': product.title,
        'batch_number': product.batch_number,
        'attributes': product.get_attributes(),
        'label_image': product.label_image
    }
    
    # Call CraftMyPDF API (placeholder - implement actual API call)
    # response = requests.post('https://api.craftmypdf.com/v1/generate', json=pdf_data)
    # pdf_url = response.json()['pdf_url']
    
    # For demonstration, create a PDF record
    pdf = models.GeneratedPDF(
        product_id=product.id,
        filename=f"{product.title}_{product.batch_number}.pdf",
        pdf_url="https://example.com/sample.pdf"  # Replace with actual URL
    )
    db.session.add(pdf)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/delete_pdf/<int:pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    pdf = models.GeneratedPDF.query.get_or_404(pdf_id)
    db.session.delete(pdf)
    db.session.commit()
    return jsonify({'success': True})

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
