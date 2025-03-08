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
    print(f"*** Processing product detail for ID: {product_id} ***")
    
    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')
    print(f"*** Filter params: category_id={category_id}, square_filter={square_filter} ***")
    
    # Create base query with the same filters as the product list page
    filtered_query = Product.query
    
    # Apply category filter if provided
    if category_id:
        filtered_query = filtered_query.join(Product.categories).filter(Category.id == int(category_id))
        print(f"*** Applied category filter: {category_id} ***")
    
    # Apply Square sync status filter if provided
    if square_filter == 'synced':
        filtered_query = filtered_query.filter(Product.square_catalog_id.isnot(None))
        print("*** Applied synced filter ***")
    elif square_filter == 'unsynced':
        filtered_query = filtered_query.filter(Product.square_catalog_id.is_(None))
        print("*** Applied unsynced filter ***")
    
    # Get all products in the filtered list in the same order as shown on the product list page
    # Sort by created_at in descending order just like the main products list
    filtered_products = filtered_query.order_by(Product.created_at.desc()).all()
    
    # Debug: Print the filtered products
    product_ids = [p.id for p in filtered_products]
    print(f"*** Filtered product IDs: {product_ids} ***")
    
    # Convert product_id to int for comparison
    product_id_int = int(product_id)
    
    # Find the current product's position in this filtered list
    current_index = -1
    for i, p in enumerate(filtered_products):
        if p.id == product_id_int:
            current_index = i
            break
    
    print(f"*** Current product ID: {product_id_int}, Found at index: {current_index} ***")
    
    # Determine previous and next products based on position in the filtered list
    previous_product = filtered_products[current_index - 1] if current_index > 0 else None
    next_product = filtered_products[current_index + 1] if current_index < len(filtered_products) - 1 else None
    
    # Debug: Print the previous and next product IDs
    prev_id = previous_product.id if previous_product else None
    next_id = next_product.id if next_product else None
    print(f"*** Previous product ID: {prev_id}, Next product ID: {next_id} ***")
    
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
