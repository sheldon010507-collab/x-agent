-- X-Agent v0 Final 数据库初始化脚本
-- V0 Final: 添加 risk_score 字段 + 内容状态流转
-- 在 Supabase SQL 编辑器中执行

-- 热点记录表 (V0 Final: 添加 risk_score)
CREATE TABLE IF NOT EXISTS trends (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    niche text NOT NULL,
    topic text NOT NULL,
    source text NOT NULL,
    score numeric NOT NULL,
    risk_score numeric DEFAULT 50.0,  -- V0 Final: 风险评分 (0-100)
    summary text,
    citations jsonb,
    url text,
    status text DEFAULT 'new',
    created_at timestamptz DEFAULT now()
);

-- 内容草稿表 (V0 Final: 状态流转 draft → confirmed/rejected)
CREATE TABLE IF NOT EXISTS content_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trend_id uuid REFERENCES trends(id),
    type text NOT NULL,
    content text NOT NULL,
    media_suggestion text,
    risk_score numeric DEFAULT 50.0,  -- V0 Final: 内容风险评分
    status text DEFAULT 'draft',  -- V0 Final: draft/confirmed/rejected/published
    confirmed_at timestamptz,     -- V0 Final: 确认时间
    rejected_at timestamptz,      -- V0 Final: 拒绝时间
    published_at timestamptz,     -- V0 Final: 发布时间
    created_at timestamptz DEFAULT now()
);

-- 每日日志表
CREATE TABLE IF NOT EXISTS daily_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    date date NOT NULL UNIQUE,
    niche text NOT NULL,
    posts_count integer DEFAULT 0,
    comments_count integer DEFAULT 0,
    likes_count integer DEFAULT 0,
    rt_count integer DEFAULT 0,
    top_engagement integer DEFAULT 0,
    notes text,
    created_at timestamptz DEFAULT now()
);

-- 策略版本表
CREATE TABLE IF NOT EXISTS strategy (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    niche text NOT NULL,
    version integer NOT NULL,
    content text NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- 自动化设置表
CREATE TABLE IF NOT EXISTS automation_settings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auto_comment boolean DEFAULT true,
    comment_daily_limit integer DEFAULT 15,
    auto_like boolean DEFAULT false,
    auto_rt boolean DEFAULT false,
    like_daily_limit integer DEFAULT 30,
    rt_daily_limit integer DEFAULT 10,
    updated_at timestamptz DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_trends_score ON trends(score DESC);
CREATE INDEX IF NOT EXISTS idx_trends_status ON trends(status);
CREATE INDEX IF NOT EXISTS idx_trends_niche ON trends(niche);
CREATE INDEX IF NOT EXISTS idx_content_queue_status ON content_queue(status);
CREATE INDEX IF NOT EXISTS idx_daily_log_date ON daily_log(date);

-- 插入默认自动化设置
INSERT INTO automation_settings (auto_comment, comment_daily_limit)
SELECT true, 15
WHERE NOT EXISTS (SELECT 1 FROM automation_settings);
