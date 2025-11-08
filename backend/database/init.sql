-- Receipt Lens Database Schema
-- PostgreSQL 15+ compatible

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS items CASCADE;
DROP TABLE IF EXISTS receipts CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Create receipts table
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_name VARCHAR(100) NOT NULL,
    purchase_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    image_hash VARCHAR(64),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create items table
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id),
    product_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,3) DEFAULT 1.0,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX idx_receipts_user_date ON receipts(user_id, purchase_date);
CREATE INDEX idx_receipts_user_id ON receipts(user_id);
CREATE INDEX idx_receipts_store ON receipts(store_name);
CREATE INDEX idx_receipts_image_hash ON receipts(image_hash);
CREATE INDEX idx_items_receipt ON items(receipt_id);
CREATE INDEX idx_items_category ON items(category_id);
CREATE INDEX idx_items_product ON items(product_name);

-- Insert default categories
INSERT INTO categories (name) VALUES
    ('bebidas'),
    ('carne'),
    ('verduras'),
    ('lácteos'),
    ('panadería'),
    ('limpieza'),
    ('ocio'),
    ('otros');

-- Create a view for analytics purposes
CREATE OR REPLACE VIEW receipt_summary AS
SELECT
    r.id,
    r.user_id,
    r.store_name,
    r.purchase_date,
    r.total_amount,
    COUNT(i.id) as item_count,
    r.created_at
FROM receipts r
LEFT JOIN items i ON r.id = i.receipt_id
GROUP BY r.id, r.user_id, r.store_name, r.purchase_date, r.total_amount, r.created_at;

-- Create a view for category spending
CREATE OR REPLACE VIEW category_spending AS
SELECT
    u.id as user_id,
    u.username,
    c.name as category_name,
    EXTRACT(YEAR FROM r.purchase_date) as year,
    EXTRACT(MONTH FROM r.purchase_date) as month,
    SUM(i.total_price) as total_spent,
    COUNT(i.id) as item_count
FROM users u
JOIN receipts r ON u.id = r.user_id
JOIN items i ON r.id = i.receipt_id
JOIN categories c ON i.category_id = c.id
GROUP BY u.id, u.username, c.name, year, month;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts for the receipt lens application';
COMMENT ON TABLE categories IS 'Product categories for classification';
COMMENT ON TABLE receipts IS 'Uploaded receipt metadata';
COMMENT ON TABLE items IS 'Individual items extracted from receipts';
COMMENT ON COLUMN receipts.image_hash IS 'SHA256 hash of uploaded image to prevent duplicates';
COMMENT ON COLUMN receipts.processed IS 'Whether the receipt has been processed by Claude AI';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Receipt Lens database schema initialized successfully!';
END $$;
