from flask import render_template
from app import app
from models import Product, Category, ProductTemplate, Settings

@app.route('/vmc-admin/')
def admin_dashboard():
    """Admin dashboard showing overview of products and categories"""
    product_count = Product.query.count()
    category_count = Category.query.count()
    template_count = ProductTemplate.query.count()
    return render_template('admin_dashboard.html', 
                         product_count=product_count,
                         category_count=category_count,
                         template_count=template_count)

@app.route('/vmc-admin/products')
def products():
    """List all products"""
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/vmc-admin/categories')
def categories():
    """List all categories"""
    categories = Category.query.all()
    return render_template('category_list.html', categories=categories)

@app.route('/vmc-admin/settings')
def settings():
    """Display and manage system settings"""
    settings = Settings.get_settings()
    return render_template('settings.html', settings=settings)
@app.route('/api/square/check-credentials')
def check_square_credentials():
    settings = Settings.get_settings()
    credentials = settings.get_active_square_credentials()
    return jsonify({'has_credentials': credentials is not None})
