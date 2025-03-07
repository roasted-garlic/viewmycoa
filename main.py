import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_app():
    """Initialize the application"""
    try:
        # Check if we're in deployment mode - define this before it's used later
        is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"
        
        # Get the workspace directory - this is where persistent storage should go
        # Using os.getcwd() ensures we're starting from the workspace root in both dev and prod
        workspace_dir = os.getcwd()
        logger.info(f"Using workspace directory: {workspace_dir}")
        
        # Create all required directories (create with exist_ok to avoid race conditions)
        # Always use relative paths from workspace root to ensure consistent paths
        static_dir = os.path.join(workspace_dir, 'static')
        uploads_dir = os.path.join(static_dir, 'uploads')
        pdfs_dir = os.path.join(static_dir, 'pdfs')
        object_storage_dir = os.path.join(static_dir, 'object_storage')
        
        # Create these directories and log their creation
        for directory in [static_dir, uploads_dir, pdfs_dir, object_storage_dir]:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Ensured directory exists at {directory}")
            except Exception as dir_error:
                logger.error(f"Failed to create directory {directory}: {str(dir_error)}")
                
        # Ensure instance directory exists for SQLite fallback
        os.makedirs(os.path.join(workspace_dir, 'instance'), exist_ok=True)
        logger.info("Ensured instance directory exists")
        
        # Initialize object storage sync if available
        try:
            import object_storage_sync
            logger.info("Initializing object storage synchronization")
            
            # If in development mode, sync existing files from object storage
            if not is_deployment:
                logger.info("Development environment detected - syncing available files from object storage")
                # Actual sync happens on-demand when images are requested
        except ImportError:
            logger.warning("Object storage sync not available - file sharing between environments disabled")
        except Exception as sync_error:
            logger.error(f"Error initializing object storage sync: {str(sync_error)}")

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

        # Configure host and port - always use port 3000 for consistency between dev and prod
        host = "0.0.0.0"  # Listen on all available interfaces
        port = int(os.getenv("PORT", 3000))  # Always default to 3000 for Replit compatibility
        
        # Check if we're in production mode
        is_production = os.getenv("REPLIT_DEPLOYMENT", "0") == "1"
        
        logger.info(f"Starting application on {host}:{port} (Production: {is_production})")
        
        # Handle environment variables for production
        if is_production:
            # Log environment variable status for deployment debugging
            env_vars = {
                "DATABASE_URL": "***" if os.environ.get("DATABASE_URL") else "Not set",
                "PGDATABASE": os.environ.get("PGDATABASE", "Not set"),
                "PGHOST": os.environ.get("PGHOST", "Not set"),
                "PGPORT": os.environ.get("PGPORT", "Not set"),
                "PGUSER": "***" if os.environ.get("PGUSER") else "Not set",
                "PGPASSWORD": "***" if os.environ.get("PGPASSWORD") else "Not set"
            }
            logger.info(f"Production environment variables: {env_vars}")
        
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
