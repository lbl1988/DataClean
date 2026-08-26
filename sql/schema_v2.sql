-- DataClean API v2 - 添加用户系统
-- 在已有的schema.sql基础上运行

-- users表（如果不存在则创建）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    name TEXT,
    plan TEXT DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 1000,
    credits_total INTEGER DEFAULT 1000,
    lemonsqueezy_customer_id TEXT,
    auth_token TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- api_keys表（如果不存在则创建）
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash TEXT UNIQUE NOT NULL,
    key_prefix TEXT NOT NULL,
    name TEXT DEFAULT 'Default',
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- api_usage表（如果不存在则创建）
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    credits_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    status_code INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- payments表（如果不存在则创建）
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lemonsqueezy_payment_id TEXT UNIQUE,
    afdian_order_id TEXT,
    amount DECIMAL(10,2) DEFAULT 0,
    credits_purchased INTEGER DEFAULT 0,
    plan TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- jobs表（如果不存在则创建）
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    input_url TEXT,
    output_url TEXT,
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_user ON api_usage(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_key ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id, created_at DESC);

-- RLS策略（允许Service Key访问所有表）
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- 允许service_role全权访问（先删后建，避免重复）
DROP POLICY IF EXISTS "service_role_all_users" ON users;
DROP POLICY IF EXISTS "service_role_all_api_keys" ON api_keys;
DROP POLICY IF EXISTS "service_role_all_api_usage" ON api_usage;
DROP POLICY IF EXISTS "service_role_all_payments" ON payments;
DROP POLICY IF EXISTS "service_role_all_jobs" ON jobs;

CREATE POLICY "service_role_all_users" ON users FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all_api_keys" ON api_keys FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all_api_usage" ON api_usage FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all_payments" ON payments FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all_jobs" ON jobs FOR ALL USING (auth.role() = 'service_role');

-- 如果users表已存在但没有auth_token字段，添加它
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS lemonsqueezy_customer_id TEXT;

-- 修复字段不匹配（如果表已存在但缺字段）
ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER;
ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS status TEXT;
ALTER TABLE api_usage ADD COLUMN IF NOT EXISTS error_message TEXT;

-- jobs表字段修复
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS input_size INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS output_size INTEGER;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS result_url TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS error_message TEXT;

