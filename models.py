from app import db
import datetime
import json

class ProductTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    attributes = db.Column(db.Text)  # Stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_attributes(self, attrs):
        self.attributes = json.dumps(attrs)

    def get_attributes(self):
        return json.loads(self.attributes) if self.attributes else {}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    batch_number = db.Column(db.String(8), nullable=False)
    sku = db.Column(db.String(8), unique=True, nullable=False)
    barcode = db.Column(db.String(12), unique=True, nullable=False)
    attributes = db.Column(db.Text)  # Stored as JSON
    label_image = db.Column(db.String(500))    # URL/path to image
    template_id = db.Column(db.Integer, db.ForeignKey('product_template.id', ondelete='SET NULL'), nullable=True)
    craftmypdf_template_id = db.Column(db.String(255))
    label_qty = db.Column(db.Integer, default=4, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Product specific fields
    mg_per_piece = db.Column(db.String(50))
    count = db.Column(db.String(50))
    per_piece_g = db.Column(db.String(50))
    net_weight_g = db.Column(db.String(50))
    cannabinoid = db.Column(db.String(100))
    qr_code = db.Column(db.String(255))
    expire_date = db.Column(db.String(50))
    disclaimer = db.Column(db.Text)
    manufactured_by = db.Column(db.String(255))

    def to_json_data(self):
        """Convert product data to JSON format for CraftMyPDF API"""
        data = {
            "cannabinoid": self.cannabinoid or "",
            "mg_per_piece": self.mg_per_piece or "",
            "count": self.count or "",
            "per_piece_g": self.per_piece_g or "",
            "net_weight_g": self.net_weight_g or "",
            "product_barcode": self.barcode,
            "sku": self.sku,
            "product_name": self.name,
            "qr_code": self.qr_code or "",
            "lot_barcode": self.batch_number,
            "expire_date": self.expire_date or "",
            "disclaimer": self.disclaimer or "",
            "manufactured_by": self.manufactured_by or ""
        }

        # Handle label image for background
        if self.label_image:
            # Ensure it's a full URL when used in the template
            data["background"] = self.label_image

        # Process dynamic attributes
        attributes = self.get_attributes()
        if attributes:
            # Add attributes in the exact format required
            for idx, (name, value) in enumerate(attributes.items()):
                data[f"product_att_name_{idx}"] = name
                data[f"product_att_name_{idx}_value"] = value

            # Create product_name_att with attributes
            attr_values = list(attributes.values())
            if attr_values:
                data["product_name_att"] = f"{self.name}: {', '.join(attr_values)}"
        else:
            data["product_name_att"] = self.name

        return data

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
