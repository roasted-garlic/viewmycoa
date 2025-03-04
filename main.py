import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_app():
    """Initialize the application"""
    try:
        # Create static and uploads directories if they don't exist
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        uploads_dir = os.path.join(static_dir, 'uploads')
        
        for directory in [static_dir, uploads_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory at {directory}")

        # SQLite will be used as a fallback in app.py when no database variables are set
        # So we don't need to error here, just ensure that directories exist
        os.makedirs('instance', exist_ok=True)
        
        # Check if we're in deployment mode - define this before it's used later
        is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"

        # Initialize database
        with app.app_context():
            import models  # Import models before creating tables
            
            # Import route modules
            import routes.auth_routes  # Import auth routes
            import routes.admin_routes  # Import admin routes
            
            # Verify database connection
            try:
                # Try a simple database operation to verify connection
                from sqlalchemy import text
                from app import db
                db.session.execute(text('SELECT 1'))
                logger.info("Database connection verified successfully")
            except Exception as db_error:
                logger.error(f"Database connection error: {str(db_error)}")
                
                if is_deployment:
                    logger.error("Deployment may fail - Please check database environment variables")
                    logger.error("See DEPLOYMENT.md for required variables")
                else:
                    logger.info("Attempting to create database tables anyway...")
            
            db.create_all()
            
            # Create default admin user if none exists
            from models import User
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@example.com', is_admin=True)
                admin.set_password('admin')  # Default password, should be changed
                db.session.add(admin)
                db.session.commit()
                logger.info("Created default admin user")
                
            logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log environment variables (excluding sensitive data)
        env_vars = {k: '***' if 'SECRET' in k or 'PASSWORD' in k or 'KEY' in k else v 
                   for k, v in os.environ.items()}
        logger.error(f"Environment variables: {env_vars}")
        raise

def main():
    """Main application entry point"""
    try:
        # Initialize the application
        init_app()

        # Configure host and port
        host = "0.0.0.0"  # Listen on all available interfaces
        port = int(os.getenv("PORT", 3000))  # Use environment port or default to 3000
        
        # Check if we're in production mode
        is_production = os.getenv("REPLIT_DEPLOYMENT", "0") == "1"
        
        logger.info(f"Starting application on {host}:{port} (Production: {is_production})")
        
        # Run the Flask application
        app.run(
            host=host,
            port=port,
            debug=not is_production,  # Disable debug mode in production
            use_reloader=not is_production  # Disable reloader in production
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
