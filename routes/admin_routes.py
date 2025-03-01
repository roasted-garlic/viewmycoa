
from flask import render_template, request, jsonify
from flask_login import login_required
from routes.auth_routes import admin_required
from app import app, db
from models import Product, Category, BatchHistory, Settings

# Admin routes can be added here if needed
# The main routes are already defined in app.py
# This file is imported in wsgi.py to ensure all routes are registered

# Example of a custom admin route that doesn't conflict with app.py
@app.route('/vmc-admin-custom')
@login_required
@admin_required
def admin_custom():
    """Custom admin page example"""
    return render_template('admin_dashboard.html')
