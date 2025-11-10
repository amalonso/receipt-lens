-- Migration: Add Admin Features
-- Date: 2025-11-10
-- Description: Add admin role, user status, API cost tracking, and activity logging

BEGIN;

-- 1. Add admin and active status to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create index for admin queries
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 2. Create API costs table for tracking AI processing costs
CREATE TABLE IF NOT EXISTS api_costs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receipt_id INTEGER REFERENCES receipts(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL, -- claude, google_vision, openai, etc.
    model VARCHAR(100), -- specific model used
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6) NOT NULL, -- cost in USD
    processing_time_ms INTEGER, -- processing time in milliseconds
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_costs_user ON api_costs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_costs_receipt ON api_costs(receipt_id);
CREATE INDEX IF NOT EXISTS idx_api_costs_created ON api_costs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_costs_provider ON api_costs(provider);

COMMENT ON TABLE api_costs IS 'Tracks API usage and costs for AI vision processing';

-- 3. Create activity logs table for audit trail
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- login, upload, delete, update_config, etc.
    entity_type VARCHAR(50), -- user, receipt, config, etc.
    entity_id INTEGER,
    details JSONB, -- additional context
    ip_address VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_entity ON activity_logs(entity_type, entity_id);

COMMENT ON TABLE activity_logs IS 'Audit trail of user and system activities';

-- 4. Create system configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string', -- string, integer, boolean, json
    category VARCHAR(50), -- vision, security, upload, general
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE, -- hide from frontend if true
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);

COMMENT ON TABLE system_config IS 'System-wide configuration settings';

-- Insert default configuration values
INSERT INTO system_config (config_key, config_value, value_type, category, description) VALUES
('vision_provider', 'claude', 'string', 'vision', 'AI provider for receipt processing'),
('max_upload_size_mb', '10', 'integer', 'upload', 'Maximum upload size in megabytes'),
('upload_rate_limit_per_hour', '50', 'integer', 'upload', 'Maximum uploads per user per hour'),
('jwt_expiration_hours', '24', 'integer', 'security', 'JWT token expiration time'),
('enable_registration', 'true', 'boolean', 'security', 'Allow new user registrations'),
('enable_duplicate_detection', 'true', 'boolean', 'upload', 'Detect and prevent duplicate receipt uploads'),
('default_currency', 'EUR', 'string', 'general', 'Default currency for receipts'),
('maintenance_mode', 'false', 'boolean', 'general', 'Enable maintenance mode')
ON CONFLICT (config_key) DO NOTHING;

-- 5. Create analytics views for admin dashboard

-- View: User statistics with receipts and spending
CREATE OR REPLACE VIEW admin_user_stats AS
SELECT
    u.id,
    u.username,
    u.email,
    u.is_admin,
    u.is_active,
    u.created_at as registered_at,
    u.last_login,
    COUNT(DISTINCT r.id) as total_receipts,
    COALESCE(SUM(r.total_amount), 0) as total_spending,
    COUNT(DISTINCT DATE(r.purchase_date)) as shopping_days,
    MIN(r.purchase_date) as first_purchase_date,
    MAX(r.purchase_date) as last_purchase_date,
    COUNT(DISTINCT r.store_name) as unique_stores,
    COALESCE(SUM(ac.cost_usd), 0) as total_api_cost
FROM users u
LEFT JOIN receipts r ON u.id = r.user_id
LEFT JOIN api_costs ac ON u.id = ac.user_id
GROUP BY u.id, u.username, u.email, u.is_admin, u.is_active, u.created_at, u.last_login;

COMMENT ON VIEW admin_user_stats IS 'Comprehensive user statistics for admin dashboard';

-- View: Daily system metrics
CREATE OR REPLACE VIEW admin_daily_metrics AS
SELECT
    DATE(created_at) as date,
    'users' as metric_type,
    COUNT(*) as count,
    0::DECIMAL(10,2) as amount
FROM users
GROUP BY DATE(created_at)
UNION ALL
SELECT
    DATE(created_at) as date,
    'receipts' as metric_type,
    COUNT(*) as count,
    COALESCE(SUM(total_amount), 0) as amount
FROM receipts
GROUP BY DATE(created_at)
UNION ALL
SELECT
    DATE(created_at) as date,
    'api_calls' as metric_type,
    COUNT(*) as count,
    COALESCE(SUM(cost_usd), 0) as amount
FROM api_costs
GROUP BY DATE(created_at)
ORDER BY date DESC, metric_type;

COMMENT ON VIEW admin_daily_metrics IS 'Daily aggregated metrics for trend analysis';

-- View: Monthly user usage summary
CREATE OR REPLACE VIEW admin_monthly_usage AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    EXTRACT(YEAR FROM r.created_at) as year,
    EXTRACT(MONTH FROM r.created_at) as month,
    COUNT(DISTINCT r.id) as receipts_count,
    COALESCE(SUM(r.total_amount), 0) as total_spending,
    COUNT(DISTINCT i.id) as items_count,
    COALESCE(SUM(ac.cost_usd), 0) as api_cost
FROM users u
LEFT JOIN receipts r ON u.id = r.user_id
LEFT JOIN items i ON r.id = i.receipt_id
LEFT JOIN api_costs ac ON u.id = ac.user_id AND DATE_TRUNC('month', ac.created_at) = DATE_TRUNC('month', r.created_at)
WHERE r.created_at IS NOT NULL
GROUP BY u.id, u.username, u.email, year, month
ORDER BY year DESC, month DESC, receipts_count DESC;

COMMENT ON VIEW admin_monthly_usage IS 'Monthly usage and costs per user';

-- View: Store analytics across all users
CREATE OR REPLACE VIEW admin_store_analytics AS
SELECT
    r.store_name,
    COUNT(DISTINCT r.user_id) as unique_users,
    COUNT(r.id) as total_receipts,
    AVG(r.total_amount) as avg_receipt_amount,
    SUM(r.total_amount) as total_revenue,
    MIN(r.purchase_date) as first_seen,
    MAX(r.purchase_date) as last_seen,
    COUNT(DISTINCT i.id) as total_items,
    AVG(i.total_price) as avg_item_price
FROM receipts r
LEFT JOIN items i ON r.id = i.receipt_id
GROUP BY r.store_name
ORDER BY total_receipts DESC;

COMMENT ON VIEW admin_store_analytics IS 'Store performance metrics across all users';

-- View: Category analytics across all users
CREATE OR REPLACE VIEW admin_category_analytics AS
SELECT
    c.id as category_id,
    c.name as category_name,
    COUNT(DISTINCT i.receipt_id) as receipts_with_category,
    COUNT(DISTINCT r.user_id) as unique_users,
    COUNT(i.id) as total_items,
    COALESCE(SUM(i.total_price), 0) as total_spending,
    AVG(i.total_price) as avg_item_price,
    AVG(i.unit_price) as avg_unit_price
FROM categories c
LEFT JOIN items i ON c.id = i.category_id
LEFT JOIN receipts r ON i.receipt_id = r.id
GROUP BY c.id, c.name
ORDER BY total_spending DESC;

COMMENT ON VIEW admin_category_analytics IS 'Category spending across all users';

-- View: Product popularity across all users
CREATE OR REPLACE VIEW admin_product_analytics AS
SELECT
    i.product_name,
    c.name as category_name,
    COUNT(DISTINCT r.user_id) as unique_buyers,
    COUNT(i.id) as purchase_count,
    SUM(i.quantity) as total_quantity,
    AVG(i.unit_price) as avg_unit_price,
    MIN(i.unit_price) as min_unit_price,
    MAX(i.unit_price) as max_unit_price,
    SUM(i.total_price) as total_revenue,
    COUNT(DISTINCT r.store_name) as available_in_stores
FROM items i
JOIN receipts r ON i.receipt_id = r.id
LEFT JOIN categories c ON i.category_id = c.id
GROUP BY i.product_name, c.name
ORDER BY purchase_count DESC;

COMMENT ON VIEW admin_product_analytics IS 'Product popularity and pricing analytics';

-- View: Recent activity feed
CREATE OR REPLACE VIEW admin_recent_activity AS
SELECT
    'receipt_uploaded' as activity_type,
    r.id as entity_id,
    u.username,
    r.store_name as description,
    r.total_amount as amount,
    r.created_at as timestamp
FROM receipts r
JOIN users u ON r.user_id = u.id
UNION ALL
SELECT
    'user_registered' as activity_type,
    u.id as entity_id,
    u.username,
    u.email as description,
    NULL as amount,
    u.created_at as timestamp
FROM users u
UNION ALL
SELECT
    'activity_log' as activity_type,
    al.id as entity_id,
    COALESCE(u.username, 'System') as username,
    al.action as description,
    NULL as amount,
    al.created_at as timestamp
FROM activity_logs al
LEFT JOIN users u ON al.user_id = u.id
ORDER BY timestamp DESC
LIMIT 100;

COMMENT ON VIEW admin_recent_activity IS 'Recent system activity feed for monitoring';

-- 6. Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 7. Add comments for new columns
COMMENT ON COLUMN users.is_admin IS 'Whether the user has administrator privileges';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active and can login';
COMMENT ON COLUMN users.last_login IS 'Timestamp of the last successful login';
COMMENT ON COLUMN users.updated_at IS 'Timestamp of the last user record update';

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Admin features migration completed successfully!';
    RAISE NOTICE 'New tables: api_costs, activity_logs, system_config';
    RAISE NOTICE 'New views: admin_user_stats, admin_daily_metrics, admin_monthly_usage, admin_store_analytics, admin_category_analytics, admin_product_analytics, admin_recent_activity';
END $$;
