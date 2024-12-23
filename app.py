import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import logging
from werkzeug.utils import secure_filename
import requests
import json
from PIL import Image
import datetime
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_only_for_development")
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Initialize extensions
from models import db
db.init_app(app)
migrate = Migrate(app, db)

# Import routes after db initialization using absolute imports
import routes.product_routes
import routes.category_routes
import routes.settings_routes

# Create tables within app context
with app.app_context():
    import models
    db.create_all()
    settings = models.Settings.get_settings()

# Basic routes for testing
@app.route('/')
def index():
    return "Label Manager is running!"

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500