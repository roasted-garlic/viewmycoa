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

        # Initialize database
        with app.app_context():
            import models  # Import models before creating tables
            db.create_all()
            db.session.commit()  # Ensure all tables are created
            logger.info("Database tables created successfully")
            
            try:
                # Create default admin user if none exists
                from models import AdminUser
                logger.info("Checking for existing admin users...")
                existing_count = AdminUser.query.count()
                logger.info(f"Found {existing_count} existing admin users")
                
                if existing_count == 0:
                    logger.info("Creating new admin user...")
                    admin = AdminUser.create(username='admin', password='admin')
                    logger.info(f"Admin user created with username: {admin.username}")
                    logger.info(f"Password hash generated: {admin.password_hash[:20]}...")
                    
                    db.session.add(admin)
                    db.session.commit()
                    
                    # Verify the user was created
                    created_admin = AdminUser.query.filter_by(username='admin').first()
                    if created_admin:
                        logger.info("Admin user successfully created and verified in database")
                    else:
                        logger.error("Failed to verify admin user after creation")
                else:
                    logger.info("Admin user already exists, skipping creation")
            except Exception as e:
                logger.error(f"Error creating admin user: {str(e)}")
                logger.exception("Full stack trace:")
                db.session.rollback()
                raise

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
        port = 5000       # Use port 5000 as specified

        logger.info(f"Starting application on {host}:{port}")
        
        # Run the Flask application
        app.run(
            host=host,
            port=port,
            debug=True,  # Enable debug mode
            use_reloader=True  # Enable auto-reload on code changes
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
