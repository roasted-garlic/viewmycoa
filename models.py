from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from flask_login import UserMixin
import datetime
import json
import werkzeug.security

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = werkzeug.security.generate_password_hash(password)
        
    def check_password(self, password):
        return werkzeug.security.check_password_hash(self.password_hash, password)

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
    square_category_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    products = db.relationship('Product', secondary=product_categories, back_populates='categories')

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
    square_catalog_id = db.Column(db.String(255), nullable=True)
    square_image_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    generated_pdfs = db.relationship('GeneratedPDF', backref='product', lazy='dynamic')
    batch_history = db.relationship('BatchHistory', backref='product', lazy='dynamic')
    categories = relationship('Category', secondary=product_categories, back_populates='products')

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


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Square integration settings
    show_square_id_controls = db.Column(db.Boolean, default=False, nullable=False)
    show_square_image_id_controls = db.Column(db.Boolean, default=False, nullable=False)
    square_environment = db.Column(db.String(20), default='sandbox', nullable=False)
    square_sandbox_access_token = db.Column(db.String(255), nullable=True)
    square_sandbox_location_id = db.Column(db.String(255), nullable=True)
    square_production_access_token = db.Column(db.String(255), nullable=True)
    square_production_location_id = db.Column(db.String(255), nullable=True)

    # CraftMyPDF integration settings - no sandbox mode
    craftmypdf_api_key = db.Column(db.String(255), nullable=True)

    @classmethod
    def get_settings(cls):
        """Get the settings instance, creating it if it doesn't exist."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def get_active_square_credentials(self):
        """Get the active Square API credentials based on current environment."""
        if self.square_environment == 'production':
            if not self.square_production_access_token or not self.square_production_location_id:
                return None
            return {
                'access_token': self.square_production_access_token,
                'location_id': self.square_production_location_id,
                'base_url': 'https://connect.squareup.com',
                'is_sandbox': False
            }

        if not self.square_sandbox_access_token or not self.square_sandbox_location_id:
            return None
        return {
            'access_token': self.square_sandbox_access_token,
            'location_id': self.square_sandbox_location_id,
            'base_url': 'https://connect.squareupsandbox.com',
            'is_sandbox': True
        }

    def get_craftmypdf_credentials(self):
        """Get the CraftMyPDF API credentials."""
        if not self.craftmypdf_api_key:
            return {'api_key': None}
        return {
            'api_key': self.craftmypdf_api_key
        }