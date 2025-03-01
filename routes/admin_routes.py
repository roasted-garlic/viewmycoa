from flask import render_template
from app import app
from models import Product, Category, ProductTemplate, Settings
from flask_login import login_required
from routes.auth_routes import admin_required, clear_login_messages

@app.route('/vmc-admin/')
@login_required
@admin_required
@clear_login_messages
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
@login_required
@admin_required
@clear_login_messages
def products():
    """List all products"""
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/vmc-admin/categories')
@login_required
@admin_required
@clear_login_messages
def categories():
    """List all categories"""
    categories = Category.query.all()
    return render_template('category_list.html', categories=categories)

@app.route('/vmc-admin/settings')
@login_required
@admin_required
@clear_login_messages
def settings():
    """Display and manage system settings"""
    settings = Settings.get_settings()
    return render_template('settings.html', settings=settings)
