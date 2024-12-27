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

# Initialize extensions after app creation
from models import db, Product, Category, ProductTemplate, Settings, BatchHistory, GeneratedPDF

db.init_app(app)
migrate = Migrate(app, db)

def init_app(app):
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal Server Error: {str(error)}")
    return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# Import routes after app initialization to avoid circular imports
from routes.admin import admin_routes
from routes.public import public_routes

app.register_blueprint(admin_routes)
app.register_blueprint(public_routes)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
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
    init_app(app)
    app.run(host='0.0.0.0', port=port, debug=True)