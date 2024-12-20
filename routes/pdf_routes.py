
from flask import jsonify, url_for
from app import app, db
from models import Product, GeneratedPDF
import os
import requests
import json
import datetime

@app.route('/api/generate_pdf/<int:product_id>', methods=['POST'])
def generate_pdf(product_id):
    # Your existing generate_pdf function code

@app.route('/api/delete_pdf/<int:pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    # Your existing delete_pdf function code
