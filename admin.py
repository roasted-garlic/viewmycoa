from functools import wraps
from flask import Blueprint, redirect, url_for, request, session, flash, render_template, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from models import Product, Category, ProductTemplate
from utils import save_image, generate_batch_number, generate_sku, generate_upc_barcode
import os
import logging

admin = Blueprint('admin', __name__, url_prefix='/vmc-admin')
logger = logging.getLogger(__name__)

def verify_password(password_hash, password):
    """Verify if the provided password matches the hash."""
    try:
        if not password_hash:
            logger.error("Password hash is empty")
            return False
        if not password_hash.startswith('pbkdf2:sha256:'):
            logger.error(f"Invalid password hash format: {password_hash[:15]}...")
            return False
        return check_password_hash(password_hash, password)
    except ValueError as e:
        logger.error(f"Password verification error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {str(e)}")
        return False

def generate_admin_hash(password):
    """Generate a proper password hash."""
    try:
        return generate_password_hash(password, method='pbkdf2:sha256')
    except Exception as e:
        logger.error(f"Error generating password hash: {str(e)}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access the admin area.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def create_default_admin():
    """Create a default admin user if none exists"""
    try:
        from models import AdminUser
        # Check if admin user exists
        if AdminUser.query.count() == 0:
            logger.info("No admin user found. Creating default admin user...")
            from werkzeug.security import generate_password_hash
            # Create admin with direct password hash
            admin = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin')
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Successfully created default admin user")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating default admin: {str(e)}")
        db.session.rollback()

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please provide both username and password', 'warning')
                return render_template('admin/login.html')
            
            # Find admin user in database
            from models import AdminUser
            admin_user = AdminUser.query.filter_by(username=username).first()
            
            if admin_user is None:
                logger.warning(f"Login attempt with invalid username: {username}")
                flash('Invalid credentials', 'danger')
                return render_template('admin/login.html')
            
            # Verify password using werkzeug's check_password_hash
            from werkzeug.security import check_password_hash
            if check_password_hash(admin_user.password_hash, password):
                logger.info(f"Successful login for admin user: {username}")
                session['admin_logged_in'] = True
                flash('Successfully logged in', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                logger.warning(f"Failed login attempt for username: {username} (invalid password)")
                flash('Invalid credentials', 'danger')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
            
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
    return render_template('admin/product_list.html', products=products, admin_view=True)

@admin.route('/templates')
@login_required
def template_list():
    templates = ProductTemplate.query.all()
    return render_template('admin/template_list.html', templates=templates)

@admin.route('/categories')
@login_required
def categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/category_list.html', categories=categories)

@admin.route('/api/categories', methods=['POST'])
@login_required
def create_category():
    try:
        data = request.get_json()
        category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        category.name = data['name']
        category.description = data.get('description', '')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

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
