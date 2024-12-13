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
        try:
            # Build the base data structure exactly matching the required format
            data = {
                "cannabinoid": self.cannabinoid or "",
                "mg_per_piece": self.mg_per_piece or "",
                "count": self.count or "",
                "per_piece_g": self.per_piece_g or "",
                "net_weight_g": self.net_weight_g or "",
                "background": "",  # Will be set in the API endpoint
                "product_barcode": int(self.barcode) if self.barcode else None,
                "sku": self.sku or "",
                "product_name": self.name,
                "product_name_att": "",  # Will be updated if attributes exist
                "product_att_name_0": "",  # Will be updated if attributes exist
                "product_att_name_0_value": "",  # Will be updated if attributes exist
                "qr_code": self.qr_code or "",
                "lot_barcode": self.batch_number,
                "expire_date": self.expire_date or "",
                "disclaimer": self.disclaimer or "",
                "manufactured_by": self.manufactured_by or ""
            }

            # Handle dynamic attributes
            attributes = self.get_attributes()
            if attributes:
                # Take the first attribute for the main product name attribute
                if len(attributes) > 0:
                    first_attr = list(attributes.items())[0]
                    data["product_att_name_0"] = first_attr[0]
                    data["product_att_name_0_value"] = str(first_attr[1])
                    data["product_name_att"] = f"{self.name}: {first_attr[1]}"

            # Ensure all values are strings except product_barcode
            cleaned_data = {}
            for key, value in data.items():
                if value is not None:
                    if key != "product_barcode":
                        cleaned_data[key] = str(value)
                    else:
                        cleaned_data[key] = value

            return cleaned_data
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error generating JSON data for product {self.id}: {str(e)}")
            raise

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
