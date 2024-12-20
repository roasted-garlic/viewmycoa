
from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Product, BatchHistory, GeneratedPDF
from utils import generate_batch_number, save_image, is_valid_image
import os
from werkzeug.utils import secure_filename
import datetime

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/product/new', methods=['GET', 'POST'])
def create_product():
    # Your existing create_product function code

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Your existing product_detail function code

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    # Your existing edit_product function code
