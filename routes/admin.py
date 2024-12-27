from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Product, Category, ProductTemplate, Settings, BatchHistory, GeneratedPDF
from werkzeug.utils import secure_filename
import os
import logging

admin_routes = Blueprint('admin', __name__)

@admin_routes.route('/vmc-admin/')
@admin_routes.route('/vmc-admin/<path:path>')
def admin_index(path=''):
    if not path:
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('admin.admin_dashboard'))

@admin_routes.route('/vmc-admin/dashboard')
def admin_dashboard():
    try:
        products = Product.query.all()
        return render_template('product_list.html', products=products)
    except Exception as e:
        logging.error(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard', 'danger')
        return render_template('product_list.html', products=[])

@admin_routes.route('/vmc-admin/products')
def products():
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('product_list.html', products=products)
    except Exception as e:
        logging.error(f"Error loading products: {str(e)}")
        flash('Error loading products', 'danger')
        return render_template('product_list.html', products=[])

# Add other admin routes here