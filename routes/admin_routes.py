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
    import sys
    from flask import session
    
    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')
    
    # Store filter parameters in session for use in navigation
    if category_id:
        session['filtered_category_id'] = category_id
    elif 'filtered_category_id' in session:
        session.pop('filtered_category_id')
        
    if square_filter:
        session['filtered_square_status'] = square_filter
    elif 'filtered_square_status' in session:
        session.pop('filtered_square_status')
    
    print(f"LIST DEBUG: Setting filter params: category={category_id}, square={square_filter}", file=sys.stderr)
    
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
    
    # Store the filtered product IDs in session for navigation
    filtered_product_ids = [p.id for p in products]
    session['filtered_product_ids'] = filtered_product_ids
    print(f"LIST DEBUG: Stored filtered products in session: {filtered_product_ids}", file=sys.stderr)
    
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
    import sys
    from flask import session
    
    product = Product.query.get_or_404(product_id)
    
    # Get filter parameters from URL or session
    category_id = request.args.get('category') 
    square_filter = request.args.get('square')
    
    # Update URL filter params with session values if not explicitly provided in URL
    if not category_id and 'filtered_category_id' in session:
        category_id = session['filtered_category_id']
        print(f"DETAIL DEBUG: Using session category: {category_id}", file=sys.stderr)
        
    if not square_filter and 'filtered_square_status' in session:
        square_filter = session['filtered_square_status']
        print(f"DETAIL DEBUG: Using session square status: {square_filter}", file=sys.stderr)
    
    # Print the filter parameters to make debugging easier
    print(f"DETAIL DEBUG: Filter parameters - category_id={category_id}, square_filter={square_filter}", file=sys.stderr)
    
    filtered_product_ids = []
    
    # Check if we have the filtered product list in session
    if 'filtered_product_ids' in session:
        # Use the stored product IDs from the list view
        filtered_product_ids = session['filtered_product_ids']
        print(f"DETAIL DEBUG: Using session filtered products: {filtered_product_ids}", file=sys.stderr)
    else:
        # If no stored list, rebuild the filtering
        # This handles direct access to product detail without going through list
        query = Product.query.order_by(Product.created_at.desc())
        
        # Apply category filter if provided
        if category_id:
            query = query.join(Product.categories).filter(Category.id == int(category_id))
            print(f"DETAIL DEBUG: Applying category filter: {category_id}", file=sys.stderr)
        
        # Apply Square sync status filter if provided
        if square_filter == 'synced':
            query = query.filter(Product.square_catalog_id.isnot(None))
            print(f"DETAIL DEBUG: Applying Square synced filter", file=sys.stderr)
        elif square_filter == 'unsynced':
            query = query.filter(Product.square_catalog_id.is_(None))
            print(f"DETAIL DEBUG: Applying Square unsynced filter", file=sys.stderr)
        
        # Get all products that match our filters
        filtered_products = query.all()
        filtered_product_ids = [p.id for p in filtered_products]
        print(f"DETAIL DEBUG: Rebuilt filtered products: {filtered_product_ids}", file=sys.stderr)
    
    # Find current product's position in the filtered list
    previous_product = None
    next_product = None
    
    try:
        current_index = filtered_product_ids.index(int(product_id))
        print(f"DETAIL DEBUG: Current product index: {current_index}", file=sys.stderr)
        
        # Get previous product
        if current_index > 0:
            previous_id = filtered_product_ids[current_index - 1]
            previous_product = Product.query.get(previous_id)
            print(f"DETAIL DEBUG: Previous product ID: {previous_id}", file=sys.stderr)
        else:
            print(f"DETAIL DEBUG: No previous product (first in list)", file=sys.stderr)
        
        # Get next product
        if current_index < len(filtered_product_ids) - 1:
            next_id = filtered_product_ids[current_index + 1]
            next_product = Product.query.get(next_id)
            print(f"DETAIL DEBUG: Next product ID: {next_id}", file=sys.stderr)
        else:
            print(f"DETAIL DEBUG: No next product (last in list)", file=sys.stderr)
    except ValueError:
        # Product not in the filtered list
        print(f"DETAIL DEBUG: Product {product_id} not found in filtered list", file=sys.stderr)
    
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
