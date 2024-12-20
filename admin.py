from functools import wraps
from flask import Blueprint, redirect, url_for, request, session, flash, render_template
from werkzeug.security import check_password_hash
from database import db
from models import Product, Category, ProductTemplate
from utils import save_image, generate_batch_number, generate_sku, generate_upc_barcode
import os

admin = Blueprint('admin', __name__, url_prefix='/vmc-admin')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get credentials from environment variables
        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if username == admin_username and admin_password_hash and check_password_hash(admin_password_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin/login.html')

@admin.route('/')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

# Product management routes
@admin.route('/products')
@login_required
def products():
    products = Product.query.all()
    return render_template('admin/product_list.html', products=products)

@admin.route('/product/new', methods=['GET', 'POST'])
@login_required
def create_product():
    templates = ProductTemplate.query.all()
    categories = Category.query.order_by(Category.name).all()
    pdf_templates = fetch_craftmypdf_templates()
    
    if request.method == 'POST':
        title = request.form.get('title')
        attributes = {}
        
        # Get selected category ID
        category_id = request.form.get('category_id')
        
        # Process dynamic attributes
        attr_names = request.form.getlist('attr_name[]')
        attr_values = request.form.getlist('attr_value[]')
        attributes = dict(zip(attr_names, attr_values))
        
        # Generate identifiers
        barcode_number = generate_upc_barcode()
        batch_number = generate_batch_number()
        sku = generate_sku()
        
        product = Product()
        product.title = title
        product.batch_number = batch_number
        product.barcode = barcode_number
        product.sku = sku
        product.cost = float(request.form.get('cost')) if request.form.get('cost') else None
        product.price = float(request.form.get('price')) if request.form.get('price') else None
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
            category = Category.query.get(category_id)
            if category:
                product.categories = [category]
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('admin.product_detail', product_id=product.id))
    
    return render_template('admin/product_create.html',
                         templates=templates,
                         categories=categories,
                         pdf_templates=pdf_templates)

# Import necessary modules and models
from flask import render_template
from models import Product, Category, ProductTemplate
from utils import generate_batch_number, generate_sku, generate_upc_barcode, save_image
from werkzeug.utils import secure_filename
