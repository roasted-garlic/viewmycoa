
from flask import Blueprint

# Import all route blueprints
from .product_routes import product_bp
from .category_routes import category_bp
from .template_routes import template_bp
from .api_routes import api_bp

# List of all blueprints to register
blueprints = [
    product_bp,
    category_bp,
    template_bp,
    api_bp
]
