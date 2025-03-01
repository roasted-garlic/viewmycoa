
from flask import render_template
from app import app
from models import Product, Category, ProductTemplate, Settings
from flask_login import login_required
from routes.auth_routes import admin_required

# Admin dashboard route is defined in app.py
# Products route is defined in app.py
# Categories route is defined in app.py

@app.route('/vmc-admin/settings')
@login_required
@admin_required
def settings():
    """Display and manage system settings"""
    settings = Settings.get_settings()
    return render_template('settings.html', settings=settings)
