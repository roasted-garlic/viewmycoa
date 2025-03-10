
"""
Deployment Instructions:

To successfully deploy this application:
1. Set these secret environment variables in the Deployments tab:
   - FLASK_SECRET_KEY: Used for session security (required)
   - DATABASE_URL: PostgreSQL connection string (recommended) 
     OR individual PostgreSQL variables:
   - PGUSER: PostgreSQL username
   - PGPASSWORD: PostgreSQL password 
   - PGHOST: PostgreSQL host
   - PGPORT: PostgreSQL port (usually 5432)
   - PGDATABASE: PostgreSQL database name

Note: If PostgreSQL variables are not set, the application will 
automatically fall back to using SQLite, which is suitable for
testing but not recommended for production.
"""


import os
import logging
from app import app, db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define is_deployment at module level so it's available globally
is_deployment = os.environ.get("REPLIT_DEPLOYMENT", "0") == "1"

# Set port for the application - always respect PORT env variable
port = int(os.environ.get("PORT", 5000))

def init_app():
    """Initialize the application"""
    try:
        # Log deployment status
        logger.info(f"Starting application in {'deployment' if is_deployment else 'development'} mode")
        logger.info(f"Using port: {port}")
        
        # Check for required environment variables in deployment mode
        if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
            missing_vars = []
            if not os.environ.get("FLASK_SECRET_KEY"):
                missing_vars.append("FLASK_SECRET_KEY")
                # Set a default value for deployment
                os.environ["FLASK_SECRET_KEY"] = "temporary-deployment-key-please-change"
                logger.warning("Set temporary FLASK_SECRET_KEY for deployment - please change in production secrets")
            
            # Check database configuration
            if not os.environ.get("DATABASE_URL"):
                # Check individual PostgreSQL variables
                pg_vars = ["PGUSER", "PGPASSWORD", "PGHOST", "PGPORT", "PGDATABASE"]
                missing_pg_vars = [var for var in pg_vars if not os.environ.get(var)]
                if missing_pg_vars:
                    missing_vars.append("PostgreSQL variables")
                    logger.warning("Missing PostgreSQL variables - will fall back to SQLite")
            
            if missing_vars:
                logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
                logger.warning("The application will run but may have limited functionality.")
                logger.warning("Refer to DEPLOYMENT.md for required variables and setup instructions.")
        
        # Get the workspace directory - this is where persistent storage should go
        # Using os.getcwd() ensures we're starting from the workspace root in both dev and prod
        workspace_dir = os.getcwd()
        logger.info(f"Using workspace directory: {workspace_dir}")
        
        # Create all required directories (create with exist_ok to avoid race conditions)
        # Always use relative paths from workspace root to ensure consistent paths
        static_dir = os.path.join(workspace_dir, 'static')
        uploads_dir = os.path.join(static_dir, 'uploads')
        pdfs_dir = os.path.join(static_dir, 'pdfs')
        
        # Create these directories and log their creation
        for directory in [static_dir, uploads_dir, pdfs_dir]:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Ensured directory exists at {directory}")
            except Exception as dir_error:
                logger.error(f"Failed to create directory {directory}: {str(dir_error)}")
                
        # Ensure instance directory exists for SQLite fallback
        os.makedirs(os.path.join(workspace_dir, 'instance'), exist_ok=True)
        logger.info("Ensured instance directory exists")

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
                    logger.warning("Database connection failed in deployment - reconfiguring to use SQLite")
                    # Reconfigure to use SQLite instead of failing
                    from app import app as flask_app
                    # Create SQLite database URL
                    sqlite_url = "sqlite:///instance/database.db"
                    logger.info(f"Setting database to SQLite: {sqlite_url}")
                    
                    # Set the SQLAlchemy Database URI
                    flask_app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url
                    
                    # Ensure instance directory exists
                    os.makedirs('instance', exist_ok=True)
                    
                    # Log the reconfiguration
                    logger.info("Reconfigured to use SQLite database for this deployment")
                    
                    # We need to re-create any disconnected sessions
                    db.session.remove()
                    db.session = db.create_scoped_session()
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

        # Configure host and port - use PORT env variable for deployment compatibility
        host = "0.0.0.0"  # Listen on all available interfaces
        # Use port from environment variable (already set at module level)
        # This ensures we respect the PORT variable set in the command
        
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
        else:
            # Only run sync in development mode
            is_development = os.environ.get("REPLIT_DEPLOYMENT", "0") != "1"
            if is_development:
                # In development mode, run startup sync in a background thread
                logger.info("Development environment detected, running startup sync")
                import threading
                import time
                import sys
                
                def delayed_startup_sync():
                    """Run startup sync with protection against duplicate runs"""
                    # Wait for app to initialize before running sync
                    time.sleep(5)
                    
                    try:
                        # Run sync using the improved startup_sync.py script
                        # which handles its own locking mechanism
                        import subprocess
                        logger.info("Starting background sync on development startup")
                        result = subprocess.run(
                            [sys.executable, "startup_sync.py"],
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minute timeout
                        )
                        
                        if result.returncode == 0:
                            logger.info("Startup sync completed successfully")
                        else:
                            logger.error(f"Startup sync failed (code {result.returncode})")
                            if result.stderr:
                                for line in result.stderr.splitlines():
                                    logger.error(f"  {line.strip()}")
                    except subprocess.TimeoutExpired:
                        logger.error("Startup sync timed out after 5 minutes")
                    except Exception as e:
                        logger.error(f"Error launching startup sync: {str(e)}")
                
                # Start sync in background thread to not block app startup
                sync_thread = threading.Thread(target=delayed_startup_sync)
                sync_thread.daemon = True  # Thread will exit when main thread exits
                sync_thread.start()
            else:
                logger.info("Production environment detected, skipping startup sync")
            
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
    try:
        # Always set missing environment variables with default values in deployment
        if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
            if not os.environ.get("FLASK_SECRET_KEY"):
                os.environ["FLASK_SECRET_KEY"] = "temporary-deployment-key-please-change"
                logger.warning("Set temporary FLASK_SECRET_KEY for deployment - please change in production secrets")
            
            # In deployment mode, add defaults for PostgreSQL variables if not set
            # This ensures our application can start even with missing variables
            os.environ.setdefault("PGUSER", "postgres")
            os.environ.setdefault("PGPASSWORD", "postgres")
            os.environ.setdefault("PGHOST", "localhost")
            os.environ.setdefault("PGPORT", "5432")
            os.environ.setdefault("PGDATABASE", "postgres")
            
            # Check database variables and provide clear error message
            pg_vars = ["PGUSER", "PGPASSWORD", "PGHOST", "PGPORT", "PGDATABASE"]
            missing_pg_vars = [var for var in pg_vars if not os.environ.get(var)]
            if missing_pg_vars and not os.environ.get("DATABASE_URL"):
                logger.warning(f"Missing PostgreSQL variables: {', '.join(missing_pg_vars)}")
                logger.warning("Will attempt to use SQLite as fallback. Add these variables in Deployments secrets for PostgreSQL.")
                # Ensure SQLite instance directory exists
                os.makedirs("instance", exist_ok=True)
                
        main()
    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")        
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
