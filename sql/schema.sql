-- DataClean API 数据库表结构
-- 在 Supabase SQL Editor 中执行

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 1000,
    credits_total INTEGER DEFAULT 1000,
    lemonsqueezy_customer_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Key表（只存哈希，不存明文）
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_prefix VARCHAR(12) NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用量记录表
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id),
    endpoint VARCHAR(50) NOT NULL,
    records_processed INTEGER NOT NULL,
    credits_used INTEGER NOT NULL,
    processing_time_ms INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 异步任务表
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    job_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    input_size INTEGER,
    output_size INTEGER,
    result_url TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 支付记录表
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    lemonsqueezy_payment_id VARCHAR(255) UNIQUE,
    afdian_order_id VARCHAR(255),
    amount DECIMAL(10, 2),
    credits_purchased INTEGER,
    plan VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_user ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
