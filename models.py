from app import db
import datetime
import json

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    attributes = db.Column(db.Text)  # Stored as JSON - contains attribute names and default values
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_attributes(self, attrs):
        self.attributes = json.dumps(attrs)

    def get_attributes(self):
        return json.loads(self.attributes) if self.attributes else {}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    batch_number = db.Column(db.String(8))
    attributes = db.Column(db.Text)  # Stored as JSON
    product_image = db.Column(db.String(500))  # URL/path to image
    label_image = db.Column(db.String(500))    # URL/path to image
    template_id = db.Column(db.Integer, db.ForeignKey('template.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    template = db.relationship('Template', backref=db.backref('products', lazy=True))

    def set_attributes(self, attrs):
        self.attributes = json.dumps(attrs)

    def get_attributes(self):
        return json.loads(self.attributes) if self.attributes else {}

class GeneratedPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pdf_url = db.Column(db.String(500))
