
import os
import sys
import requests
import shutil
import logging
from models import Product, GeneratedPDF
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PDFSync")

# Define the base URL of your production site
PRODUCTION_URL = "https://viewmycoa.com"  # This is the correct production URL


def ensure_dir_exists(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def download_pdf(url, save_path):
    """Download a PDF from a URL and save it to a path"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            # Verify PDF was downloaded correctly by checking file size
            file_size = os.path.getsize(save_path)
            if file_size > 0:
                logger.info(f"Successfully downloaded PDF ({file_size} bytes): {save_path}")
                return True
            else:
                logger.error(f"Downloaded file is empty: {save_path}")
                # Remove the invalid file
                os.remove(save_path)
                return False
        else:
            logger.error(
                f"Failed to download {url} - Status code: {response.status_code}"
            )
            return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False


def sync_product_pdfs(product_ids=None):
    """Sync product PDFs from production to development
    
    Args:
        product_ids: Optional list of product IDs to sync. If None, syncs all products.
    """
    with app.app_context():
        # Query products
        query = Product.query
        if product_ids:
            query = query.filter(Product.id.in_(product_ids))

        products = query.all()
        logger.info(f"Found {len(products)} products to process")

        # Track valid PDF paths to use for cleanup later
        valid_pdf_paths = set()
        
        success_count = 0
        for product in products:
            product_id = product.id
            batch_number = product.batch_number
            
            # Get all PDFs for this product
            pdfs = GeneratedPDF.query.filter_by(product_id=product_id).all()
            
            for pdf in pdfs:
                if pdf.filename:
                    # Extract batch number from filename (typical format: label_BATCH_TIMESTAMP.pdf)
                    batch_dir = os.path.join('static', 'pdfs', batch_number)
                    ensure_dir_exists(batch_dir)
                    
                    save_path = os.path.join(batch_dir, pdf.filename)
                    
                    # Track this as a valid PDF path
                    valid_pdf_paths.add(save_path)
                    
                    # Only download if file doesn't exist locally
                    if not os.path.exists(save_path):
                        # Construct URL based on filename structure - add missing slash
                        pdf_url = f"{PRODUCTION_URL}/static/pdfs/{batch_number}/{pdf.filename}"
                        logger.info(f"Downloading PDF for product ID {product_id}: {pdf_url}")
                        if download_pdf(pdf_url, save_path):
                            success_count += 1
                    else:
                        logger.info(f"PDF already exists locally: {save_path}")

            # Also check batch history for PDFs
            from models import BatchHistory
            batch_histories = BatchHistory.query.filter_by(product_id=product_id).all()
            for history in batch_histories:
                history_batch = history.batch_number
                history_pdfs = GeneratedPDF.query.filter_by(batch_history_id=history.id).all()
                
                for pdf in history_pdfs:
                    if pdf.filename:
                        # Handle historical PDFs
                        batch_dir = os.path.join('static', 'pdfs', history_batch)
                        ensure_dir_exists(batch_dir)
                        
                        save_path = os.path.join(batch_dir, pdf.filename)
                        
                        # Track this as a valid PDF path
                        valid_pdf_paths.add(save_path)
                        
                        # Only download if file doesn't exist locally
                        if not os.path.exists(save_path):
                            pdf_url = f"{PRODUCTION_URL}/static/pdfs/{history_batch}/{pdf.filename}"
                            logger.info(f"Downloading historical PDF: {pdf_url}")
                            if download_pdf(pdf_url, save_path):
                                success_count += 1
                        else:
                            logger.info(f"Historical PDF already exists locally: {save_path}")

        # Clean up orphaned PDFs
        cleanup_count = clean_orphaned_pdfs(valid_pdf_paths)

        logger.info(
            f"PDF sync complete. Downloaded {success_count} PDFs, removed {cleanup_count} orphaned PDFs."
        )


def clean_orphaned_pdfs(valid_pdf_paths):
    """
    Remove PDF files that exist in development but not in production.
    
    Args:
        valid_pdf_paths: Set of PDF paths that should be kept
        
    Returns:
        Number of files removed
    """
    cleanup_count = 0
    pdfs_dir = os.path.join('static', 'pdfs')
    
    # Only clean if PDFs directory exists
    if not os.path.exists(pdfs_dir):
        return 0
        
    # Iterate through batch directories
    for batch_dir in os.listdir(pdfs_dir):
        batch_path = os.path.join(pdfs_dir, batch_dir)
        
        # Skip if not a directory
        if not os.path.isdir(batch_path):
            continue
            
        # Check each file in the batch directory
        for filename in os.listdir(batch_path):
            file_path = os.path.join(batch_path, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Check if file is in our valid paths list
            if file_path not in valid_pdf_paths:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed orphaned PDF: {file_path}")
                    cleanup_count += 1
                except OSError as e:
                    logger.error(f"Error removing orphaned PDF {file_path}: {str(e)}")
    
    # Clean up empty batch directories
    for batch_dir in os.listdir(pdfs_dir):
        batch_path = os.path.join(pdfs_dir, batch_dir)
        if os.path.isdir(batch_path) and not os.listdir(batch_path):
            try:
                os.rmdir(batch_path)
                logger.info(f"Removed empty batch directory: {batch_path}")
            except OSError as e:
                logger.error(f"Error removing empty batch directory {batch_path}: {str(e)}")
    
    return cleanup_count


if __name__ == "__main__":
    # Allow passing product IDs as arguments
    product_ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]

    if product_ids:
        logger.info(f"Syncing PDFs for specific product IDs: {product_ids}")
        sync_product_pdfs(product_ids)
    else:
        logger.info("Syncing PDFs for all products")
        sync_product_pdfs()
