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
        try:
            # Ensure we're using an integer for filtering
            category_id_int = int(category_id)
            query = query.join(Product.categories).filter(Category.id == category_id_int)
        except (ValueError, TypeError):
            app.logger.warning(f"Invalid category_id parameter: {category_id}")

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

@app.route('/vmc-admin/products/detail/<int:product_id>')
@login_required
def admin_product_detail(product_id):
    """Show product detail with filter preservation"""
    product = Product.query.get_or_404(product_id)

    # Get filter parameters
    category_id = request.args.get('category')
    square_filter = request.args.get('square')

    # Add debug logging to help troubleshoot
    app.logger.debug(f"Filtering with category_id: {category_id}, square_filter: {square_filter}")

    # Flag for template to determine if filters are active
    has_filters = bool(category_id or square_filter)
    app.logger.debug(f"has_filters flag: {has_filters}")

    # Start with base query - use same ordering as products_list view
    query = Product.query.order_by(Product.created_at.desc())

    # Apply category filter if provided
    if category_id:
        try:
            # Ensure we're using an integer for filtering
            category_id_int = int(category_id)
            app.logger.debug(f"Applying category filter with ID: {category_id_int}")
            query = query.join(Product.categories).filter(Category.id == category_id_int)
        except (ValueError, TypeError):
            app.logger.warning(f"Invalid category_id parameter: {category_id}")
            has_filters = False  # Reset flag if category filter is invalid

    # Apply Square sync status filter if provided
    if square_filter == 'synced':
        app.logger.debug("Applying 'synced' Square filter")
        query = query.filter(Product.square_catalog_id.isnot(None))
    elif square_filter == 'unsynced':
        app.logger.debug("Applying 'unsynced' Square filter")
        query = query.filter(Product.square_catalog_id.is_(None))
    else:
        # If neither synced nor unsynced, we don't have a square filter
        if square_filter:
            app.logger.warning(f"Invalid square_filter parameter: {square_filter}")
            if not category_id:
                has_filters = False  # Reset flag if square filter is invalid and no category filter

    # Get all products that match our filters in the exact order shown in the product list
    filtered_products = query.all()
    app.logger.debug(f"Found {len(filtered_products)} products after filtering")

    # Initialize previous and next products
    previous_product = None
    next_product = None

    # Only attempt to find previous/next products if we have filters
    if has_filters:
        # Log filtered products to help with debugging
        app.logger.debug(f"Filtered products count: {len(filtered_products)}")
        app.logger.debug(f"Current filters - Category: {category_id}, Square: {square_filter}")
        filtered_ids = [p.id for p in filtered_products]
        app.logger.debug(f"Filtered product IDs: {filtered_ids}")

        # Find the current product's index in the filtered list
        current_index = None
        for i, p in enumerate(filtered_products):
            if p.id == product_id:
                current_index = i
                app.logger.debug(f"Found current product at index {i} of filtered list")
                break

        # Set previous and next products based on position in filtered list
        if current_index is not None:
            # Get previous product (if not first)
            if current_index > 0:
                previous_product = filtered_products[current_index - 1]
                app.logger.debug(f"Previous product ID: {previous_product.id}")
            else:
                app.logger.debug("No previous product - this is the first in filtered list")
                # Explicitly set previous to None to ensure it's clear
                previous_product = None

            # Get next product (if not last)
            if current_index < len(filtered_products) - 1:
                next_product = filtered_products[current_index + 1]
                app.logger.debug(f"Next product ID: {next_product.id}")
            else:
                app.logger.debug("No next product - this is the last in filtered list")
                # Explicitly set next to None to ensure it's clear
                next_product = None
        else:
            app.logger.warning(f"Current product ID {product_id} not found in filtered list!")
            # If current product isn't in filtered list, don't show filtered navigation
            has_filters = False
    else:
        # If no filters are applied, use simple ID-based navigation
        # For non-filtered view, the navigation is based on ID
        # Previous product is the one with next highest ID (newer)
        # Next product is the one with next lowest ID (older)
        next_product = Product.query.filter(Product.id < product_id).order_by(Product.id.desc()).first()
        previous_product = Product.query.filter(Product.id > product_id).order_by(Product.id.asc()).first()

    # Get all PDFs for this product
    from models import GeneratedPDF, BatchHistory

    pdfs = GeneratedPDF.query.filter(
        GeneratedPDF.product_id == product_id
    ).order_by(GeneratedPDF.created_at.desc()).all()

    # Add debug logging for final template variables
    app.logger.debug(f"Final template variables - previous_product: {previous_product.id if previous_product else None}, next_product: {next_product.id if next_product else None}, has_filters: {has_filters}")

    return render_template('product_detail.html', 
                         product=product, 
                         pdfs=pdfs,
                         previous_product=previous_product,
                         next_product=next_product,
                         BatchHistory=BatchHistory,
                         selected_category=category_id,
                         square_filter=square_filter,
                         has_filters=has_filters)