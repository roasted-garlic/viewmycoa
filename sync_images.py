import os
import sys
import requests
import shutil
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ImageSync")

# Define the base URL of your production site
# Change this to your actual production URL
PRODUCTION_URL = "https://viewmycoa.com/"  # Update this!


def ensure_dir_exists(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def download_image(url, save_path):
    """Download an image from a URL and save it to a path"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            # Verify image was downloaded correctly by attempting to open it
            try:
                img = Image.open(save_path)
                img.verify()  # Verify it's a valid image
                logger.info(
                    f"Successfully downloaded and verified: {save_path}")
                return True
            except Exception as img_error:
                logger.error(
                    f"Downloaded file is not a valid image: {save_path} - {str(img_error)}"
                )
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


def sync_product_images(product_ids=None):
    """Sync product images from production to development
    
    Args:
        product_ids: Optional list of product IDs to sync. If None, syncs all products.
    """
    from models import Product
    from app import app

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

            # Process product image
            if product.product_image:
                # Create product directory
                product_dir = os.path.join('static', 'uploads',
                                           str(product_id))
                ensure_dir_exists(product_dir)

                # Get image filename from path
                filename = os.path.basename(product.product_image)
                save_path = os.path.join(product_dir, filename)

                # Only download if file doesn't exist locally
                if not os.path.exists(save_path):
                    image_url = f"{PRODUCTION_URL}/static/{product.product_image}"
                    logger.info(
                        f"Downloading product image for product ID {product_id}: {image_url}"
                    )
                    if download_image(image_url, save_path):
                        success_count += 1
                else:
                    logger.info(
                        f"Product image already exists locally: {save_path}")

            # Process label image
            if product.label_image:
                # Create product directory
                product_dir = os.path.join('static', 'uploads',
                                           str(product_id))
                ensure_dir_exists(product_dir)

                # Get image filename from path
                filename = os.path.basename(product.label_image)
                save_path = os.path.join(product_dir, filename)

                # Only download if file doesn't exist locally
                if not os.path.exists(save_path):
                    image_url = f"{PRODUCTION_URL}/static/{product.label_image}"
                    logger.info(
                        f"Downloading label image for product ID {product_id}: {image_url}"
                    )
                    if download_image(image_url, save_path):
                        success_count += 1
                else:
                    logger.info(
                        f"Label image already exists locally: {save_path}")

        logger.info(
            f"Image sync complete. Successfully downloaded {success_count} images."
        )


if __name__ == "__main__":
    # Allow passing product IDs as arguments
    product_ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]

    if product_ids:
        logger.info(f"Syncing images for specific product IDs: {product_ids}")
        sync_product_images(product_ids)
    else:
        logger.info("Syncing images for all products")
        sync_product_images()
