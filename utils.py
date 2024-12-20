import os
from werkzeug.utils import secure_filename

import random
import string
from PIL import Image
import io
from werkzeug.utils import secure_filename

def generate_upc_barcode():
    """Generate a random UPC-A barcode number"""
    digits = ''.join(random.choices(string.digits, k=11))
    return digits + calculate_upc_check_digit(digits)

def calculate_upc_check_digit(digits):
    """Calculate the check digit for a UPC-A barcode"""
    total = 0
    for i, digit in enumerate(digits):
        total += int(digit) * (3 if i % 2 else 1)
    check_digit = (10 - (total % 10)) % 10
    return str(check_digit)

def generate_sku():
    """Generate a unique SKU"""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{numbers}"

def clean_filename(filename):
    """Clean and secure a filename"""
    return secure_filename(filename)

def is_valid_image(file):
    """Check if file is a valid image"""
    try:
        Image.open(file)
        return True
    except:
        return False

def process_image(file):
    """Process and optimize image"""
    img = Image.open(file)
    output = io.BytesIO()
    img.save(output, format=img.format, optimize=True)
    output.seek(0)
    return output

def generate_batch_number():
    """Generate a unique batch number"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

def save_image(file, product_id, image_type):
    """Save an uploaded image file and return the relative path"""
    if not file:
        return None
        
    # Get file extension
    filename = secure_filename(file.filename)
    _, ext = os.path.splitext(filename)
    
    # Generate new filename using product ID and image type
    new_filename = f"{image_type}_{product_id}{ext}"
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join('static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    filepath = os.path.join(upload_dir, new_filename)
    
    # Process and optimize the image
    img = Image.open(file)
    img.save(os.path.join(filepath), optimize=True)
    
    # Return relative path from static directory
    return os.path.join('uploads', new_filename)