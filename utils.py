import string
import random
import os
from PIL import Image
from io import BytesIO
import base64
import barcode
from barcode.writer import ImageWriter

def generate_batch_number():
    """Generate a random 8-character alphanumeric batch number"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

def process_image(image_file, max_size=(800, 800)):
    """Process and optimize uploaded images"""
    try:
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size)
        
        # Optimize image
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        return output
        
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

def is_valid_image(file):
    """Validate image file"""
    try:
        img = Image.open(file)
        img.verify()
        return True
    except:
        return False

def clean_filename(filename):
    """Clean and sanitize filename"""
    valid_chars = f"-_.{string.ascii_letters}{string.digits}"
    cleaned = ''.join(c for c in filename if c in valid_chars)
    return cleaned[:255]  # Limit length to 255 characters

def format_file_size(size):
    """Format file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
def generate_upc_barcode():
    """Generate a random 12-digit UPC-A barcode"""
    # Generate first 11 digits randomly
    digits = ''.join(random.choice(string.digits) for _ in range(11))
    
    # Calculate check digit
    sum_odd = sum(int(digits[i]) for i in range(0, 11, 2))
    sum_even = sum(int(digits[i]) for i in range(1, 11, 2))
    total = sum_odd * 3 + sum_even
    check_digit = (10 - (total % 10)) % 10
    
    # Return complete UPC-A code
    return digits + str(check_digit)

def save_barcode(barcode_number):
    """Generate and save a barcode image"""
    upc = barcode.get('upc', barcode_number, writer=ImageWriter())
    filename = f'barcode_{barcode_number}'
    filepath = os.path.join('static', 'uploads', filename)
    upc.save(filepath)
    return f'uploads/{filename}'
    return f"{size:.1f} GB"
