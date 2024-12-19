
import os

def cleanup_original_images():
    # Path to uploads directory
    uploads_dir = os.path.join('static', 'uploads')
    
    # Files to preserve (files in product-specific directories)
    preserved_paths = set()
    
    # Collect all files in product-specific directories
    for item in os.listdir(uploads_dir):
        full_path = os.path.join(uploads_dir, item)
        if os.path.isdir(full_path) and item.isdigit():
            # This is a product directory, preserve its contents
            for file in os.listdir(full_path):
                preserved_paths.add(os.path.join(full_path, file))
    
    # Remove files in root uploads directory
    for item in os.listdir(uploads_dir):
        full_path = os.path.join(uploads_dir, item)
        if os.path.isfile(full_path) and full_path not in preserved_paths:
            try:
                os.remove(full_path)
                print(f"Removed: {item}")
            except Exception as e:
                print(f"Error removing {item}: {str(e)}")

if __name__ == "__main__":
    cleanup_original_images()
