import os
import sys
import requests
import shutil
import re
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ImageSync")

# Define the base URL of your production site
PRODUCTION_URL = "https://viewmycoa.com"  # This is the correct production URL


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
    # Skip sync in production environment - first safety check
    if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
        logger.warning("Attempting to run image sync in production environment - aborting")
        return

    from models import Product
    from app import app

    with app.app_context():
        # Double-check the environment inside the app context - second safety check
        if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
            logger.warning("Attempting to run image sync in production environment - aborting")
            return

        # Log the environment to make it clear
        env_type = "PRODUCTION" if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1" else "DEVELOPMENT"
        logger.info(f"Running in {env_type} environment")

        # Query products
        query = Product.query
        if product_ids:
            query = query.filter(Product.id.in_(product_ids))

        products = query.all()
        logger.info(f"Found {len(products)} products to process")

        # Track valid image paths to use for cleanup later
        valid_image_paths = set()

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

                # Keep track of this valid image
                valid_image_paths.add(save_path)

                # Check if file exists with timestamp suffix pattern
                base_name, ext = os.path.splitext(filename)
                timestamp_pattern = f"{base_name}_[0-9]{{10}}{ext}"
                existing_files = [f for f in os.listdir(product_dir) if os.path.isfile(os.path.join(product_dir, f))]

                # When we have the exact filename already, let's still verify it's a valid image
                if os.path.exists(save_path):
                    try:
                        # Verify the existing file is a valid image
                        img = Image.open(save_path)
                        img.verify()
                        logger.info(f"Existing image verified as valid: {save_path}")
                    except Exception as img_error:
                        # If not valid, mark it for re-download
                        logger.warning(f"Existing image file is invalid, will re-download: {save_path} - {str(img_error)}")
                        os.remove(save_path)

                # Find timestamped versions if they exist and use them
                timestamp_files = [f for f in existing_files if re.match(timestamp_pattern, f)]
                if timestamp_files and not os.path.exists(save_path):
                    # Use the most recent timestamped file
                    most_recent = sorted(timestamp_files)[-1]
                    logger.info(f"Found timestamped version of image: {most_recent} for {filename}")

                    # Verify the timestamped file is a valid image before using it
                    timestamped_path = os.path.join(product_dir, most_recent)
                    try:
                        img = Image.open(timestamped_path)
                        img.verify()
                        # Copy the valid timestamped file
                        if not os.path.exists(save_path):
                            shutil.copy2(timestamped_path, save_path)
                            logger.info(f"Created copy from verified timestamped version: {save_path}")
                    except Exception as img_error:
                        logger.warning(f"Timestamped image file is invalid, will not use: {timestamped_path} - {str(img_error)}")
                        # Remove invalid timestamped file
                        os.remove(timestamped_path)

                # Only download if file doesn't exist locally in any form
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

                # Keep track of this valid image
                valid_image_paths.add(save_path)

                # Check if file exists with timestamp suffix pattern
                base_name, ext = os.path.splitext(filename)
                timestamp_pattern = f"{base_name}_[0-9]{{10}}{ext}"
                existing_files = [f for f in os.listdir(product_dir) if os.path.isfile(os.path.join(product_dir, f))]

                # When we have the exact filename already, let's still verify it's a valid image
                if os.path.exists(save_path):
                    try:
                        # Verify the existing file is a valid image
                        img = Image.open(save_path)
                        img.verify()
                        logger.info(f"Existing image verified as valid: {save_path}")
                    except Exception as img_error:
                        # If not valid, mark it for re-download
                        logger.warning(f"Existing image file is invalid, will re-download: {save_path} - {str(img_error)}")
                        os.remove(save_path)

                # Find timestamped versions if they exist and use them
                timestamp_files = [f for f in existing_files if re.match(timestamp_pattern, f)]
                if timestamp_files and not os.path.exists(save_path):
                    # Use the most recent timestamped file
                    most_recent = sorted(timestamp_files)[-1]
                    logger.info(f"Found timestamped version of image: {most_recent} for {filename}")

                    # Verify the timestamped file is a valid image before using it
                    timestamped_path = os.path.join(product_dir, most_recent)
                    try:
                        img = Image.open(timestamped_path)
                        img.verify()
                        # Copy the valid timestamped file
                        if not os.path.exists(save_path):
                            shutil.copy2(timestamped_path, save_path)
                            logger.info(f"Created copy from verified timestamped version: {save_path}")
                    except Exception as img_error:
                        logger.warning(f"Timestamped image file is invalid, will not use: {timestamped_path} - {str(img_error)}")
                        # Remove invalid timestamped file
                        os.remove(timestamped_path)

                # Only download if file doesn't exist locally in any form
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

        # Clean up orphaned images
        cleanup_count = clean_orphaned_images(valid_image_paths)

        logger.info(
            f"Image sync complete. Downloaded {success_count} images, removed {cleanup_count} orphaned images."
        )

def clean_orphaned_images(valid_image_paths):
    """
    Remove image files that exist in development but not in production.
    Only runs in development environment.

    Args:
        valid_image_paths: Set of image paths that should be kept

    Returns:
        Number of files removed
    """
    # Skip cleanup in production environment
    if os.environ.get("REPLIT_DEPLOYMENT", "0") == "1":
        logger.info("Skipping orphaned image cleanup in production environment")
        return 0

    cleanup_count = 0
    uploads_dir = os.path.join('static', 'uploads')

    # Only clean if uploads directory exists
    if not os.path.exists(uploads_dir):
        return 0

    # Iterate through product directories
    for product_dir in os.listdir(uploads_dir):
        product_path = os.path.join(uploads_dir, product_dir)

        # Skip if not a directory or not a product ID directory
        if not os.path.isdir(product_path) or not product_dir.isdigit():
            continue

        # Check each file in the product directory
        for filename in os.listdir(product_path):
            file_path = os.path.join(product_path, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Check if file is in our valid paths list
            if file_path not in valid_image_paths:
                try:
                    # Extra safety check to ensure we're in development
                    if os.environ.get("REPLIT_DEPLOYMENT", "0") == "0":
                        os.remove(file_path)
                        logger.info(f"[DEV] Removed orphaned image: {file_path}")
                        cleanup_count += 1
                except OSError as e:
                    logger.error(f"Error removing orphaned image {file_path}: {str(e)}")

    return cleanup_count


if __name__ == "__main__":
    # Allow passing product IDs as arguments
    product_ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]

    if product_ids:
        logger.info(f"Syncing images for specific product IDs: {product_ids}")
        sync_product_images(product_ids)
    else:
        logger.info("Syncing images for all products")
        sync_product_images()