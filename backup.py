
import os
import sys
import datetime
import shutil
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup():
    # Generate timestamp for backup folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join('backups', timestamp)
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Created backup directory: {backup_dir}")
    
    # Backup SQLite database
    try:
        # Create database backup
        db_file = os.path.join('instance', 'database.db')
        if os.path.exists(db_file):
            # Connect to the database
            conn = sqlite3.connect(db_file)
            # Backup the database to SQL file
            with open(os.path.join(backup_dir, 'db_backup.sql'), 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            conn.close()
            logger.info(f"Database backup created successfully")
        else:
            logger.warning(f"Database file not found at {db_file}")
    except Exception as e:
        logger.error(f"Error backing up database: {str(e)}")
    
    # Backup uploads folder
    try:
        uploads_dir = os.path.join('static', 'uploads')
        if os.path.exists(uploads_dir):
            uploads_backup_dir = os.path.join(backup_dir, 'uploads')
            shutil.copytree(uploads_dir, uploads_backup_dir)
            logger.info(f"Uploads folder backed up successfully")
        else:
            logger.warning(f"Uploads directory not found at {uploads_dir}")
    except Exception as e:
        logger.error(f"Error backing up uploads folder: {str(e)}")
    
    # Backup PDFs folder
    try:
        pdfs_dir = os.path.join('static', 'pdfs')
        if os.path.exists(pdfs_dir):
            pdfs_backup_dir = os.path.join(backup_dir, 'pdfs')
            shutil.copytree(pdfs_dir, pdfs_backup_dir)
            logger.info(f"PDFs folder backed up successfully")
        else:
            logger.warning(f"PDFs directory not found at {pdfs_dir}")
    except Exception as e:
        logger.error(f"Error backing up PDFs folder: {str(e)}")
    
    logger.info(f"Backup completed: {backup_dir}")
    return timestamp

if __name__ == "__main__":
    create_backup()
