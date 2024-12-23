from flask import jsonify, request
from app import app
from models import db, Product, Category

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'sku': p.sku,
        'price': p.price
    } for p in products])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'title': product.title,
        'sku': product.sku,
        'price': product.price,
        'attributes': product.get_attributes()
    })
