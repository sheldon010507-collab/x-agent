-- X-Agent v3.0 数据库初始化脚本
-- 创建 6 张核心表：trends, content_queue, daily_log, strategy, automation_settings, llm_config
-- 执行时间：2026-03-25

-- ========== 1. trends 表 - 热点记录表 ==========
CREATE TABLE IF NOT EXISTS trends (
    id UUID PRIMARY KEY,
    niche VARCHAR(50) NOT NULL DEFAULT 'general',
    topic VARCHAR(500) NOT NULL,
    source VARCHAR(100),
    score DECIMAL(5,2) NOT NULL DEFAULT 0,
    summary TEXT,
    citations JSONB,
    url TEXT,
    relevance DECIMAL(5,2) DEFAULT 0,
    velocity DECIMAL(5,2) DEFAULT 0,
    authority DECIMAL(5,2) DEFAULT 0,
    convergence DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_trends_score ON trends(score DESC);
CREATE INDEX idx_trends_status ON trends(status);
CREATE INDEX idx_trends_niche ON trends(niche);
CREATE INDEX idx_trends_created_at ON trends(created_at DESC);

-- ========== 2. content_queue 表 - 内容队列表 ==========
CREATE TABLE IF NOT EXISTS content_queue (
    id UUID PRIMARY KEY,
    trend_id UUID REFERENCES trends(id) ON DELETE CASCADE,
    type VARCHAR(10) NOT NULL, -- A/B/C
    content TEXT NOT NULL,
    media_suggestion VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft',
    niche VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_content_status ON content_queue(status);
CREATE INDEX idx_content_niche ON content_queue(niche);
CREATE INDEX idx_content_type ON content_queue(type);
CREATE INDEX idx_content_created_at ON content_queue(created_at DESC);

-- ========== 3. daily_log 表 - 每日日志表 ==========
CREATE TABLE IF NOT EXISTS daily_log (
    id UUID PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    posts_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    rt_count INTEGER DEFAULT 0,
    top_engagement INTEGER DEFAULT 0,
    notes TEXT,
    niche VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_daily_log_date ON daily_log(date DESC);
CREATE INDEX idx_daily_log_niche ON daily_log(niche);

-- ========== 4. strategy 表 - 策略版本表 ==========
CREATE TABLE IF NOT EXISTS strategy (
    id UUID PRIMARY KEY,
    niche VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(niche, version)
);

-- 索引优化
CREATE INDEX idx_strategy_niche ON strategy(niche);
CREATE INDEX idx_strategy_version ON strategy(version DESC);

-- ========== 5. automation_settings 表 - 自动化设置表 ==========
CREATE TABLE IF NOT EXISTS automation_settings (
    id UUID PRIMARY KEY,
    auto_comment BOOLEAN DEFAULT TRUE,
    comment_daily_limit INTEGER DEFAULT 15,
    auto_like BOOLEAN DEFAULT FALSE,
    like_daily_limit INTEGER DEFAULT 30,
    auto_rt BOOLEAN DEFAULT FALSE,
    rt_daily_limit INTEGER DEFAULT 10,
    auto_post BOOLEAN DEFAULT FALSE,
    post_schedule_enabled BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== 6. llm_config 表 - LLM 配置表 ==========
CREATE TABLE IF NOT EXISTS llm_config (
    id UUID PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_llm_config_provider ON llm_config(provider);
CREATE INDEX idx_llm_config_active ON llm_config(is_active);

-- ========== 初始化数据 ==========

-- 初始化自动化设置
INSERT INTO automation_settings (id, auto_comment, comment_daily_limit, auto_like, auto_rt, auto_post, updated_at)
VALUES (gen_random_uuid(), TRUE, 15, FALSE, FALSE, FALSE, NOW())
ON CONFLICT DO NOTHING;

-- 初始化 LLM 配置（默认 Anthropic）
INSERT INTO llm_config (id, provider, model, is_active, temperature, max_tokens, created_at, updated_at)
VALUES (gen_random_uuid(), 'anthropic', 'claude-3-5-sonnet-20241022', TRUE, 0.7, 4096, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ========== 注释说明 ==========
COMMENT ON TABLE trends IS '热点记录表 - 存储采集的热点数据及 4 维评分';
COMMENT ON TABLE content_queue IS '内容队列表 - 存储待发布的内容草稿';
COMMENT ON TABLE daily_log IS '每日日志表 - 记录每日运营数据';
COMMENT ON TABLE strategy IS '策略版本表 - 存储内容策略版本';
COMMENT ON TABLE automation_settings IS '自动化设置表 - 控制自动化功能开关';
COMMENT ON TABLE llm_config IS 'LLM 配置表 - 配置 LLM 供应商和参数';

COMMENT ON COLUMN trends.relevance IS 'Relevance(40%): 文本相关性/语义相似度';
COMMENT ON COLUMN trends.velocity IS 'Velocity(30%): 24h 互动增速';
COMMENT ON COLUMN trends.authority IS 'Authority(15%): 作者权威性/来源可信度';
COMMENT ON COLUMN trends.convergence IS 'Convergence(15%): 跨平台汇聚性';

-- ========== 完成 ==========
