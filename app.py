import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import logging
from werkzeug.utils import secure_filename
import requests
import json
from PIL import Image
import datetime
from flask_migrate import Migrate
from utils import generate_batch_number, is_valid_image
from models import db, product_categories

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

# Initialize SQLAlchemy with app
db.init_app(app)
migrate = Migrate(app, db)

# Create tables within app context
with app.app_context():
    import models
    db.create_all()
    settings = models.Settings.get_settings()

# Add basic routes for testing
@app.route('/')
def index():
    return "Label Manager is running!"