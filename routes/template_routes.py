
from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import ProductTemplate

@app.route('/templates')
def template_list():
    # Your existing template_list function code

@app.route('/template/new', methods=['GET', 'POST'])
def create_template():
    # Your existing create_template function code
