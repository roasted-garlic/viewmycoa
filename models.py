
from app import db
import datetime
import json

class ProductTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    attributes = db.Column(db.Text)  # Stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_attributes(self, attrs):
        if attrs is None:
            self.attributes = json.dumps({})
        elif isinstance(attrs, (dict, list)):
            self.attributes = json.dumps(attrs)
        elif isinstance(attrs, str):
            try:
                # Parse string to ensure it's valid JSON and convert back
                parsed = json.loads(attrs)
                self.attributes = json.dumps(parsed)
            except json.JSONDecodeError:
                self.attributes = json.dumps({})
        else:
            self.attributes = json.dumps({})

    def get_attributes(self):
        if not self.attributes:
            return {}
        try:
            return json.loads(self.attributes)
        except json.JSONDecodeError:
            return {}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    batch_number = db.Column(db.String(8))
    sku = db.Column(db.String(8), unique=True)  # SKU format similar to batch number
    barcode = db.Column(db.String(12), unique=True)  # UPC-A is 12 digits
    attributes = db.Column(db.Text)  # Stored as JSON
    product_image = db.Column(db.String(500))  # URL/path to image
    label_image = db.Column(db.String(500))    # URL/path to image
    coa_pdf = db.Column(db.String(500))      # URL/path to COA PDF
    template_id = db.Column(db.Integer, db.ForeignKey('product_template.id', ondelete='SET NULL'), nullable=True)
    craftmypdf_template_id = db.Column(db.String(255))
    label_qty = db.Column(db.Integer, default=4, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    generated_pdfs = db.relationship('GeneratedPDF', backref='product', lazy='dynamic')

    def set_attributes(self, attrs):
        if attrs is None:
            self.attributes = json.dumps({})
        elif isinstance(attrs, (dict, list)):
            self.attributes = json.dumps(attrs)
        elif isinstance(attrs, str):
            try:
                # Parse string to ensure it's valid JSON and convert back
                parsed = json.loads(attrs)
                self.attributes = json.dumps(parsed)
            except json.JSONDecodeError:
                self.attributes = json.dumps({})
        else:
            self.attributes = json.dumps({})

    def get_attributes(self):
        if not self.attributes:
            return {}
        try:
            return json.loads(self.attributes)
        except json.JSONDecodeError:
            return {}

class GeneratedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pdf_url = db.Column(db.String(500))
