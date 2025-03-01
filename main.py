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
            import routes.auth_routes  # Import auth routes
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

        # Configure host
        host = "0.0.0.0"  # Listen on all available interfaces
        
        # Try different ports
        import socket
        ports = [5000, 5001, 5002, 5003, 8080]
        port = None
        
        for test_port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((host, test_port))
                s.close()
                port = test_port
                logger.info(f"Found free port: {port}")
                break
            except socket.error:
                logger.info(f"Port {test_port} is in use, trying next port")
                continue
        
        if port is None:
            port = 8080  # Fallback to 8080 if all are taken
            logger.warning(f"All preferred ports in use, using fallback port: {port}")
        
        logger.info(f"Starting application on {host}:{port}")
        
        # Run the Flask application
        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=True
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
