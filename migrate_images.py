
from app import app, db
from models import Product
import os
import shutil

def migrate_product_images():
    with app.app_context():
        products = Product.query.all()
        for product in products:
            # Create product-specific directory
            product_dir = os.path.join('static', 'uploads', str(product.id))
            os.makedirs(product_dir, exist_ok=True)

            # Handle product image
            if product.product_image and not product.product_image.startswith(f'uploads/{product.id}/'):
                try:
                    old_path = os.path.join('static', product.product_image)
                    if os.path.exists(old_path):
                        ext = os.path.splitext(product.product_image)[1]
                        new_filename = f'product_image_{product.id}{ext}'
                        new_path = os.path.join(product_dir, new_filename)
                        shutil.copy2(old_path, new_path)
                        product.product_image = os.path.join('uploads', str(product.id), new_filename)

                except Exception as e:
                    print(f"Error moving product image for product {product.id}: {str(e)}")

            # Handle label image
            if product.label_image and not product.label_image.startswith(f'uploads/{product.id}/'):
                try:
                    old_path = os.path.join('static', product.label_image)
                    if os.path.exists(old_path):
                        ext = os.path.splitext(product.label_image)[1]
                        new_filename = f'label_image_{product.id}{ext}'
                        new_path = os.path.join(product_dir, new_filename)
                        shutil.copy2(old_path, new_path)
                        product.label_image = os.path.join('uploads', str(product.id), new_filename)

                except Exception as e:
                    print(f"Error moving label image for product {product.id}: {str(e)}")

        db.session.commit()

if __name__ == "__main__":
    migrate_product_images()
