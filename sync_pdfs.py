
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
                    
                    # Only download if file doesn't exist locally
                    if not os.path.exists(save_path):
                        # Construct URL based on filename structure
                        pdf_url = f"{PRODUCTION_URL}static/pdfs/{batch_number}/{pdf.filename}"
                        logger.info(f"Downloading PDF for product ID {product_id}: {pdf_url}")
                        if download_pdf(pdf_url, save_path):
                            success_count += 1
                    else:
                        logger.info(f"PDF already exists locally: {save_path}")

        logger.info(
            f"PDF sync complete. Successfully downloaded {success_count} PDFs."
        )


if __name__ == "__main__":
    # Allow passing product IDs as arguments
    product_ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]

    if product_ids:
        logger.info(f"Syncing PDFs for specific product IDs: {product_ids}")
        sync_product_pdfs(product_ids)
    else:
        logger.info("Syncing PDFs for all products")
        sync_product_pdfs()
