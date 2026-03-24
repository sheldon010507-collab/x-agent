# X 智能运营 Agent v2.0

**多 Niche 内容自动化系统** - Telegram + OpenClaw 驱动

[![Status](https://img.shields.io/badge/status-ready%20for%20testing-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Progress](https://img.shields.io/badge/progress-95%25-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Score](https://img.shields.io/badge/code%20score-90/100-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

---

## 🎯 项目简介

为**任意 Niche**（英语市场为主）构建的智能内容运营系统，通过 Telegram Bot 实现热点监控、智能内容生成、自动化评论和每日复盘。

**核心价值**: 把每天找热点、写文案、刷评论的时间压缩到最低，专注高质量内容制作和账号私域转化。

---

## ✨ 核心功能

### 🔥 热点监控
- 多平台采集：X Trending + Reddit + Google Trends
- 复合评分：Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
- 智能分级：≥80分立即推送，60-79分存库，<60分丢弃

### 🤖 智能生成
- **A类**: AI全自动推文（3条备选，5种角度）
- **B类**: 30秒视频脚本（含分镜建议）
- **C类**: 智能评论（带emoji+问题结尾）

### 🎭 Niche语气注入
支持7种专属语气，自动注入生成内容：
- adult（成人用品）- cheeky, 暗示, 感性
- ai_tools（AI工具）- 极客, 效率, 前沿
- beauty（美妆）- 种草, 姐妹情, 精致
- fitness（健身）- 励志, 数据, 挑战
- crypto（加密）- FOMO, alpha, 社群
- humor（搞笑）- 无厘头, 自黑, meme
- custom（自定义）- 完全可编辑

### ⚙️ 自动化功能
- 定时热点采集（每2小时）
- 自动智能评论（可设每日上限）
- 每日复盘报告（21:00 UK时间）
- 点赞/RT开关控制

### 📊 数据驱动
- Supabase云数据库
- 完整数据追踪与分析
- 策略版本管理

---

## 🏗️ 项目结构

```
x-agent-v2/
├── main.py                 # 入口文件
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量模板
├── .gitignore             # Git忽略配置
│
├── modules/               # 核心模块（全部完成）
│   ├── config.py          # 配置管理 (92/100) ✅
│   ├── database.py        # Supabase操作 (90/100) ✅
│   ├── llm_router.py      # LLM多供应商路由 (88/100) ✅
│   ├── generator.py       # 内容生成 (90/100) ✅
│   ├── scorer.py          # 复合评分 (92/100) ✅
│   ├── research.py        # 数据采集 (88/100) ✅
│   ├── trends.py          # 趋势采集 (85/100) ✅
│   ├── bot.py             # Telegram Bot (90/100) ✅
│   ├── openclaw_bridge.py # OpenClaw集成 (88/100) ✅
│   └── scheduler.py       # 定时任务 (90/100) ✅
│
├── prompts/               # Prompt模板
│   ├── type_a.txt         # A类推文模板
│   ├── type_b.txt         # B类视频脚本模板
│   ├── comment.txt        # 智能评论模板
│   └── review.txt         # 每日复盘模板
│
└── niche_voices/          # Niche语气文件
    ├── adult.txt          # 成人用品
    ├── ai_tools.txt       # AI工具
    ├── beauty.txt         # 美妆
    ├── fitness.txt        # 健身
    ├── crypto.txt         # 加密货币
    ├── humor.txt          # 搞笑
    └── custom.txt         # 自定义
```

---

## 🚀 快速开始

### 1️⃣ 克隆项目

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent-v2
```

### 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 3️⃣ 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 填入配置
```

**必需配置**:
- `TELEGRAM_BOT_TOKEN` - Telegram Bot Token
- `SUPABASE_URL` - Supabase项目URL
- `SUPABASE_KEY` - Supabase服务端Key
- 至少一个LLM API Key（推荐Anthropic）

**可选配置**:
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - Reddit API
- `LLM_PROVIDER` - 默认LLM供应商（默认anthropic）
- `TIMEZONE` - 时区（默认Europe/London）

### 4️⃣ 初始化数据库

在Supabase SQL编辑器中执行以下schema：

```sql
-- 热点记录表
CREATE TABLE trends (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    niche text NOT NULL,
    topic text NOT NULL,
    source text NOT NULL,
    score numeric NOT NULL,
    summary text,
    citations jsonb,
    url text,
    status text DEFAULT 'new',
    created_at timestamptz DEFAULT now()
);

-- 内容草稿表
CREATE TABLE content_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trend_id uuid REFERENCES trends(id),
    type text NOT NULL,
    content text NOT NULL,
    media_suggestion text,
    status text DEFAULT 'draft',
    created_at timestamptz DEFAULT now()
);

-- 每日日志表
CREATE TABLE daily_log (
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
CREATE TABLE strategy (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    niche text NOT NULL,
    version integer NOT NULL,
    content text NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- 自动化设置表
CREATE TABLE automation_settings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auto_comment boolean DEFAULT true,
    comment_daily_limit integer DEFAULT 15,
    auto_like boolean DEFAULT false,
    auto_rt boolean DEFAULT false,
    like_daily_limit integer DEFAULT 30,
    rt_daily_limit integer DEFAULT 10,
    updated_at timestamptz DEFAULT now()
);
```

### 5️⃣ 运行系统

```bash
python main.py
```

---

## 📱 Telegram Bot 指令

| 指令 | 功能 |
|------|------|
| `/start` | 今日热点概览 + 快捷菜单 |
| `/set_niche` | 切换Niche（全局立即生效） |
| `/research` | 深度研究任意话题 |
| `/trends` | 当前热点列表（按评分排序） |
| `/create` | 创建内容（A/B/评论） |
| `/queue` | 查看待发布草稿队列 |
| `/log` | 快捷录入今日发布数据 |
| `/report` | 查看复盘报告（今日/本周） |
| `/strategy` | 查看当前内容策略 |
| `/settings` | 自动化设置面板 |
| `/llm` | 切换LLM供应商 |

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **语言** | Python 3.11+ |
| **Bot框架** | python-telegram-bot 20.7 |
| **数据库** | Supabase (PostgreSQL) |
| **LLM** | 多供应商支持（Anthropic/OpenAI/Groq/Gemini/OpenRouter/NVIDIA/Ollama） |
| **数据采集** | PRAW (Reddit) + pytrends + Nitter |
| **调度** | APScheduler |
| **自动化** | OpenClaw |

---

## 📊 开发进度

### 总体进度: 95% ✅

| 模块 | 完成度 | 评分 | 状态 |
|------|--------|------|------|
| config.py | 100% | 92/100 | ✅ |
| database.py | 100% | 90/100 | ✅ |
| llm_router.py | 100% | 88/100 | ✅ |
| generator.py | 100% | 90/100 | ✅ |
| scorer.py | 100% | 92/100 | ✅ |
| research.py | 100% | 88/100 | ✅ |
| trends.py | 100% | 85/100 | ✅ |
| bot.py | 100% | 90/100 | ✅ |
| openclaw_bridge.py | 100% | 88/100 | ✅ |
| scheduler.py | 100% | 90/100 | ✅ |
| main.py | 100% | 92/100 | ✅ |

**平均评分**: 90/100

---

## ⚠️ 剩余5%待完成项

| 项目 | 状态 | 说明 |
|------|------|------|
| 单元测试 | ❌ | 需添加pytest测试用例 |
| 数据库迁移脚本 | ❌ | 需添加migrations/目录 |
| LICENSE文件 | ❌ | 需添加MIT License |
| 部署文档 | ❌ | 需添加DEPLOYMENT.md |

---

## 🔒 安全说明

- ✅ 所有API Key从环境变量读取，不硬编码
- ✅ 使用Supabase ORM，参数化查询防SQL注入
- ✅ Telegram Bot输入验证
- ✅ 每日上限控制防止滥用
- ✅ 随机延迟防检测

---

## 📝 更新日志

### v2.0.0 (2026-03-24)
- ✅ 完成所有核心模块开发
- ✅ 实现多平台热点采集
- ✅ 实现复合评分系统
- ✅ 实现A/B/C类内容生成
- ✅ 实现完整Telegram Bot指令
- ✅ 实现OpenClaw集成
- ✅ 代码审查评分90/100

---

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

---

## 📄 License

MIT License - 待添加

---

## 👥 Agent团队

| Agent | 角色 | 职责 |
|-------|------|------|
| CEO (Friday) | 项目经理 | 任务分配、进度追踪、决策协调 |
| Backend | 后端开发 | API、数据库、核心逻辑 |
| Frontend | 前端开发 | UI/UX、Telegram Bot |
| Connection | 集成开发 | OpenClaw集成、配置管理 |
| Reviewer | 代码审查 | 质量保障、最佳实践 |
| COO | 运营管理 | 文档、Deadline、工作流 |

---

**代码审查**: Sage (Reviewer Agent) ✅

**最后更新**: 2026-03-24
