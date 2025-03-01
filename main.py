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

        # Check for deployment mode with missing database URL
        is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
        db_url = os.environ.get("DATABASE_URL") 
        
        if is_deployment and not db_url:
            # Check if we have individual Postgres variables
            pg_user = os.environ.get("PGUSER")
            pg_password = os.environ.get("PGPASSWORD")
            pg_database = os.environ.get("PGDATABASE")
            
            if not (pg_user and pg_password and pg_database):
                logger.error("DEPLOYMENT ERROR: Missing required database environment variables")
                logger.error("Please set DATABASE_URL or PGUSER, PGPASSWORD, PGDATABASE, PGHOST, PGPORT")
                # We'll continue but the app will use the fallback SQLite DB which is not ideal for production

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
        raise

def main():
    """Main application entry point"""
    try:
        # Initialize the application
        init_app()

        # Configure host and port
        host = "0.0.0.0"  # Listen on all available interfaces
        port = int(os.getenv("PORT", 5000))  # Use environment port or default to 5000
        
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
