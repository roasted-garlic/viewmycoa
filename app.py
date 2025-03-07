
import os
import logging
from flask import Flask, render_template, url_for, redirect, flash, request, session, send_from_directory
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Product, Category, ProductTemplate, Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Flask application
app = Flask(__name__)

# Set up the SQLAlchemy database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development-secret-key')

# Handle file uploads
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['PDF_FOLDER'] = os.path.join(os.getcwd(), 'static', 'pdfs')

# Initialize database
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register error handlers
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Configure file serving for development environment
@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    # Check if using object storage for cross-environment sharing
    try:
        import object_storage_sync
        # Only try to sync images in development mode
        if os.environ.get("REPLIT_DEPLOYMENT", "0") != "1":
            object_storage_sync.maybe_sync_file_from_storage('uploads', filename)
    except (ImportError, Exception) as e:
        logger.warning(f"Could not sync file from object storage: {str(e)}")
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    # Check if using object storage for cross-environment sharing
    try:
        import object_storage_sync
        # Only try to sync PDFs in development mode
        if os.environ.get("REPLIT_DEPLOYMENT", "0") != "1":
            object_storage_sync.maybe_sync_file_from_storage('pdfs', filename)
    except (ImportError, Exception) as e:
        logger.warning(f"Could not sync file from object storage: {str(e)}")
    
    return send_from_directory(app.config['PDF_FOLDER'], filename)

# Import routes to register them with the app
with app.app_context():
    try:
        # Import route modules - this is done inside app_context to avoid circular imports
        from routes import auth_routes, admin_routes
        logger.info("Routes loaded successfully")
    except Exception as e:
        logger.error(f"Error loading routes: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
