from flask import Blueprint, render_template, request, current_app
from models import Product, BatchHistory, db
import logging

public_routes = Blueprint('public', __name__)

@public_routes.route('/')
def index():
    return render_template('search_home.html')

@public_routes.route('/search')
def search_results():
    query = request.args.get('q', '')
    try:
        products = Product.query.filter(
            (Product.title.ilike(f'%{query}%')) |
            (Product.batch_number.ilike(f'%{query}%'))
        ).all()

        batch_history = BatchHistory.query.filter(
            BatchHistory.batch_number.ilike(f'%{query}%')
        ).all()

        return render_template('search_results.html',
                            products=products,
                            batch_history=batch_history,
                            query=query)
    except Exception as e:
        current_app.logger.error(f"Error in search: {str(e)}")
        return render_template('search_results.html',
                            products=[],
                            batch_history=[],
                            query=query)

@public_routes.route('/batch/<batch_number>')
def public_product_detail(batch_number):
    try:
        product = Product.query.filter_by(batch_number=batch_number).first()
        if product:
            return render_template('public_product_detail.html', 
                                product=product, 
                                is_historical=False)

        history = BatchHistory.query.filter_by(batch_number=batch_number).first_or_404()
        return render_template('public_product_detail.html', 
                            product=history.product,
                            batch_history=history,
                            is_historical=True)
    except Exception as e:
        current_app.logger.error(f"Error in product detail: {str(e)}")
        return "Error loading product details", 500