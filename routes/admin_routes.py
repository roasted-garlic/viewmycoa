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
    
    # Start with base query, sorted by created_at descending (newest first)
    query = Product.query.order_by(Product.created_at.desc())
    
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
    app.logger.info(f"Processing product detail for ID: {product_id}")
    
    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')
    app.logger.info(f"Filter params: category_id={category_id}, square_filter={square_filter}")
    
    # Build a query to get the filtered products in the proper order
    # Start with a base query for products
    query = Product.query
    
    # Apply category filter if provided
    if category_id:
        query = query.join(Product.categories).filter(Category.id == int(category_id))
    
    # Apply Square sync status filter if provided
    if square_filter == 'synced':
        query = query.filter(Product.square_catalog_id.isnot(None))
    elif square_filter == 'unsynced':
        query = query.filter(Product.square_catalog_id.is_(None))
    
    # Order by created_at descending (newest first)
    query = query.order_by(Product.created_at.desc())
    
    # Get the IDs of all products in the filtered list
    filtered_products = query.all()
    filtered_product_ids = [p.id for p in filtered_products]
    
    app.logger.info(f"Found {len(filtered_product_ids)} products in filter")
    app.logger.info(f"Filtered product IDs: {filtered_product_ids}")
    
    # Find current product position
    try:
        current_index = filtered_product_ids.index(int(product_id))
        app.logger.info(f"Current product at position {current_index} in filtered list")
        
        # Get previous and next product objects
        previous_id = filtered_product_ids[current_index - 1] if current_index > 0 else None
        next_id = filtered_product_ids[current_index + 1] if current_index < len(filtered_product_ids) - 1 else None
        
        previous_product = Product.query.get(previous_id) if previous_id else None
        next_product = Product.query.get(next_id) if next_id else None
        
        app.logger.info(f"Previous product ID: {previous_id}, Next product ID: {next_id}")
    except ValueError:
        app.logger.warning(f"Product {product_id} not found in filtered list")
        previous_product = None
        next_product = None
    
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
