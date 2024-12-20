
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Product, BatchHistory
from app import db
import os

product_bp = Blueprint('product', __name__)

@product_bp.route('/vmc-admin/products')
def products():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@product_bp.route('/vmc-admin/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    pdfs = GeneratedPDF.query.filter(
        GeneratedPDF.product_id == product_id
    ).order_by(GeneratedPDF.created_at.desc()).all()
    return render_template('product_detail.html', 
                         product=product, 
                         pdfs=pdfs, 
                         BatchHistory=BatchHistory)

# Add other product-related routes here
