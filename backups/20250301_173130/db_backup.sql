BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE batch_history (
	id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	batch_number VARCHAR(8) NOT NULL, 
	attributes TEXT, 
	coa_pdf VARCHAR(500), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE
);
CREATE TABLE category (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	square_category_id VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE generated_pdf (
	id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	batch_history_id INTEGER, 
	filename VARCHAR(255) NOT NULL, 
	created_at DATETIME, 
	pdf_url VARCHAR(500), 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE, 
	FOREIGN KEY(batch_history_id) REFERENCES batch_history (id) ON DELETE CASCADE
);
CREATE TABLE product (
	id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	batch_number VARCHAR(8), 
	sku VARCHAR(8), 
	barcode VARCHAR(12), 
	attributes TEXT, 
	cost FLOAT, 
	price FLOAT, 
	product_image VARCHAR(500), 
	label_image VARCHAR(500), 
	coa_pdf VARCHAR(500), 
	template_id INTEGER, 
	craftmypdf_template_id VARCHAR(255), 
	label_qty INTEGER NOT NULL, 
	square_catalog_id VARCHAR(255), 
	square_image_id VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (sku), 
	UNIQUE (barcode), 
	FOREIGN KEY(template_id) REFERENCES product_template (id) ON DELETE SET NULL
);
CREATE TABLE product_categories (
	product_id INTEGER, 
	category_id INTEGER, 
	FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES category (id) ON DELETE CASCADE
);
CREATE TABLE product_template (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	attributes TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE TABLE settings (
	id INTEGER NOT NULL, 
	show_square_id_controls BOOLEAN NOT NULL, 
	show_square_image_id_controls BOOLEAN NOT NULL, 
	square_environment VARCHAR(20) NOT NULL, 
	square_sandbox_access_token VARCHAR(255), 
	square_sandbox_location_id VARCHAR(255), 
	square_production_access_token VARCHAR(255), 
	square_production_location_id VARCHAR(255), 
	craftmypdf_api_key VARCHAR(255), 
	PRIMARY KEY (id)
);
INSERT INTO "settings" VALUES(1,0,0,'sandbox',NULL,NULL,NULL,NULL,NULL);
COMMIT;
