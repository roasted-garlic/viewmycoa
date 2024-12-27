import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_key_replace_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('static', 'pdfs'), exist_ok=True)

# Initialize extensions after app creation but before routes
from models import db

def init_db():
    """Initialize database and verify connection"""
    try:
        db.init_app(app)
        with app.app_context():
            db.engine.connect()
            logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

def init_migrations():
    """Initialize Flask-Migrate"""
    try:
        migrate = Migrate(app, db)
        with app.app_context():
            migrate.init_app(app, db, compare_type=True)
            logger.info("Migration system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Migration initialization error: {str(e)}")
        return False

# Initialize database and migrations
if not init_db():
    raise SystemExit("Failed to initialize database")
if not init_migrations():
    raise SystemExit("Failed to initialize migrations")

# Import routes after app initialization to avoid circular imports
from routes.admin import admin_routes
from routes.public import public_routes

app.register_blueprint(admin_routes)
app.register_blueprint(public_routes)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    try:
        pdf_dir = os.path.join('static', 'pdfs')
        file_path = os.path.join(pdf_dir, filename)

        if not os.path.exists(file_path):
            app.logger.error(f"PDF not found at path: {file_path}")
            return "PDF not found", 404

        download = request.args.get('download', '0') == '1'
        return send_from_directory(
            pdf_dir, 
            filename,
            as_attachment=download,
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Error serving PDF {filename}: {str(e)}")
        return f"Error accessing PDF: {str(e)}", 500

# Initialize the app when running directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=True)