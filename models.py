from database import db
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
            # Convert simple name list to dict with optional values
            if isinstance(attrs, list):
                attrs = {name: "" for name in attrs}
            self.attributes = json.dumps(attrs)
        elif isinstance(attrs, str):
            try:
                parsed = json.loads(attrs)
                if isinstance(parsed, list):
                    parsed = {name: "" for name in parsed}
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

# Association table for Product-Category relationship
product_categories = db.Table('product_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id', ondelete='CASCADE')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'))
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    products = db.relationship('Product', secondary=product_categories, backref=db.backref('categories', lazy='dynamic'))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    batch_number = db.Column(db.String(8))
    sku = db.Column(db.String(8), unique=True)  # SKU format similar to batch number
    barcode = db.Column(db.String(12), unique=True)  # UPC-A is 12 digits
    attributes = db.Column(db.Text)  # Stored as JSON
    cost = db.Column(db.Float, nullable=True)  # Product cost (optional)
    price = db.Column(db.Float, nullable=True)  # Product price (optional)
    product_image = db.Column(db.String(500))  # URL/path to image
    label_image = db.Column(db.String(500))    # URL/path to image
    coa_pdf = db.Column(db.String(500))      # URL/path to COA PDF
    template_id = db.Column(db.Integer, db.ForeignKey('product_template.id', ondelete='SET NULL'), nullable=True)
    craftmypdf_template_id = db.Column(db.String(255))
    label_qty = db.Column(db.Integer, default=4, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    generated_pdfs = db.relationship('GeneratedPDF', backref='product', lazy='dynamic')
    batch_history = db.relationship('BatchHistory', backref='product', lazy='dynamic')
    # Categories relationship is handled through the backref in Category model

    def set_attributes(self, attrs):
        if attrs is None:
            self.attributes = json.dumps({})
        elif isinstance(attrs, (dict, list)):
            # Convert simple name list to dict with optional values
            if isinstance(attrs, list):
                attrs = {name: "" for name in attrs}
            self.attributes = json.dumps(attrs)
        elif isinstance(attrs, str):
            try:
                parsed = json.loads(attrs)
                if isinstance(parsed, list):
                    parsed = {name: "" for name in parsed}
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

class BatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    batch_number = db.Column(db.String(8), nullable=False)
    attributes = db.Column(db.Text)  # Stored as JSON
    coa_pdf = db.Column(db.String(500))  # URL/path to COA PDF
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_attributes(self, attrs):
        if attrs is None:
            self.attributes = json.dumps({})
        elif isinstance(attrs, (dict, list)):
            self.attributes = json.dumps(attrs)
        elif isinstance(attrs, str):
            try:
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
    batch_history_id = db.Column(db.Integer, db.ForeignKey('batch_history.id', ondelete='CASCADE'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pdf_url = db.Column(db.String(500))
    batch_history = db.relationship('BatchHistory', backref='pdfs')
