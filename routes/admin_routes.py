from flask import render_template, request
from app import app
from models import Product, Category, ProductTemplate, Settings
from flask_login import login_required
from routes.auth_routes import admin_required

@app.route('/vmc-admin/overview')
@login_required
def admin_overview():
    """Admin dashboard showing overview of products and categories"""
    product_count = Product.query.count()
    category_count = Category.query.count()
    template_count = ProductTemplate.query.count()
    return render_template('admin_dashboard.html', 
                         product_count=product_count,
                         category_count=category_count,
                         template_count=template_count)

@app.route('/vmc-admin/products-list')
@app.route('/vmc-admin/products')
@login_required
@admin_required
def products_list():
    """List all products with optional filtering"""
    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')
    
    # Start with base query
    query = Product.query
    
    # Apply category filter if provided
    if category_id:
        query = query.join(Product.categories).filter(Category.id == category_id)
    
    # Apply Square sync status filter if provided
    if square_filter == 'synced':
        query = query.filter(Product.square_catalog_id.isnot(None))
    elif square_filter == 'unsynced':
        query = query.filter(Product.square_catalog_id.is_(None))
    
    # Get all products with applied filters
    products = query.all()
    
    # Get all categories for the dropdown
    categories = Category.query.all()
    
    return render_template('product_list.html', 
                          products=products, 
                          categories=categories, 
                          selected_category=category_id,
                          square_filter=square_filter)

@app.route('/vmc-admin/categories-list')
@login_required
@admin_required
def categories_list():
    """List all categories"""
    categories = Category.query.all()
    return render_template('category_list.html', categories=categories)

@app.route('/vmc-admin/settings-page')
@login_required
@admin_required
def settings_page():
    """Display and manage system settings"""
    settings = Settings.get_settings()
    return render_template('settings.html', settings=settings)

@app.route('/vmc-admin/products/<int:product_id>')
@login_required
def admin_product_detail(product_id):
    """Show product detail with filter preservation"""
    product = Product.query.get_or_404(product_id)
    
    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')
    
    # Start with base query for previous and next products
    prev_query = Product.query
    next_query = Product.query
    
    # Apply category filter if provided
    if category_id:
        prev_query = prev_query.join(Product.categories).filter(Category.id == category_id)
        next_query = next_query.join(Product.categories).filter(Category.id == category_id)
    
    # Apply Square sync status filter if provided
    if square_filter == 'synced':
        prev_query = prev_query.filter(Product.square_catalog_id.isnot(None))
        next_query = next_query.filter(Product.square_catalog_id.isnot(None))
    elif square_filter == 'unsynced':
        prev_query = prev_query.filter(Product.square_catalog_id.is_(None))
        next_query = next_query.filter(Product.square_catalog_id.is_(None))
    
    # Get previous and next products within the filtered set
    previous_product = prev_query.filter(Product.id < product_id).order_by(Product.id.desc()).first()
    next_product = next_query.filter(Product.id > product_id).order_by(Product.id.asc()).first()
    
    # Get all PDFs for this product
    from models import GeneratedPDF, BatchHistory
    
    pdfs = GeneratedPDF.query.filter(
        GeneratedPDF.product_id == product_id
    ).order_by(GeneratedPDF.created_at.desc()).all()
    
    return render_template('product_detail.html', 
                         product=product, 
                         pdfs=pdfs,
                         previous_product=previous_product,
                         next_product=next_product,
                         BatchHistory=BatchHistory,
                         selected_category=category_id,
                         square_filter=square_filter)
