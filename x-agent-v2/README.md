# X-Agent v2.0

**X (Twitter) 热点监控 + 智能内容生产 + 自动复盘系统**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Completion](https://img.shields.io/badge/completion-95%25-brightgreen)](https://github.com/sheldon010507-collab/x-agent/blob/main/CODE_REVIEW_COMPLETE.md)
[![Code Quality](https://img.shields.io/badge/code%20quality-90/100-blue)](https://github.com/sheldon010507-collab/x-agent/blob/main/CODE_REVIEW_COMPLETE.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📖 简介

X-Agent v2.0 是一个**多 Niche 内容自动化运营系统**，基于 Telegram + OpenClaw 驱动，实现：

- 🔥 **热点监控**: 多平台采集（X + Reddit + Google Trends），复合评分筛选
- 🤖 **智能生成**: A 类推文 / B 类视频脚本 / C 类评论，AI 自动生成
- 🎭 **Niche 语气**: 7 种专属语气风格（成人用品、AI 工具、美妆、健身、加密、搞笑、自定义）
- ⚙️ **自动化**: 定时采集、自动评论、智能发布、每日复盘

**核心价值**: 把每天找热点、写文案、刷评论的时间压缩到最低，专注高质量 B 类内容制作和账号私域转化。

---

## ✨ 核心功能

### 1. 热点采集与评分

**多平台数据源**:
- X (Twitter) Trending - UK/US
- Reddit - 多 Subreddit
- Google Trends - UK/US
- 自定义关键词监控

**复合评分公式** (满分 100):
```
总分 = Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
```

**智能推送策略**:
- **≥80 分**: 立即 Telegram 推送 + 自动生成评论
- **60-79 分**: 存库，每日 21:00 汇总展示
- **<60 分**: 自动丢弃

### 2. 内容生成（3 种类型）

#### A 类 - AI 全自动推文
- 每次生成 3 条备选
- 支持角度：Hot take / Data / Interactive Poll / Product Recommendation / Cheeky
- 自动带相关 hashtag
- 符合 Niche 语气风格

#### B 类 - 视频脚本
- 30 秒分镜脚本（精确到秒）
- 包含：开场钩子 (0-5s) + 主体内容 (5-20s) + CTA(20-30s)
- 配图关键词建议
- 最佳发布时间建议（UK 时间）

#### C 类 - 智能评论
- 长度 ≤ 120 字符
- 必带 emoji + 问题结尾（提升回复率）
- 30% 概率自然带 CTA
- OpenClaw 自动执行（随机延迟 10-30 秒防检测）

### 3. Niche 语气注入

| Niche | 语气风格 | 典型句式 |
|-------|---------|---------|
| **adult** | cheeky、暗示、感性、大胆 | "you deserve this 😏" |
| **ai_tools** | 极客、效率、前沿、干货 | "unpopular opinion:" |
| **beauty** | 种草、姐妹情、精致、真实测评 | "girlies this is worth every penny 💅" |
| **fitness** | 励志、数据、挑战、社群 | "no excuses." |
| **crypto** | FOMO、alpha、社群信任 | "not financial advice but…" |
| **humor** | 无厘头、自黑、meme 引用 | "me: *does thing* also me:" |
| **custom** | 用户自定义 | 完全自定义 |

### 4. Telegram Bot 交互

**完整指令集** (12 个指令):
- `/start` - 今日热点概览 + 快捷菜单
- `/set_niche` - 切换 Niche（全局立即生效）
- `/research` - 立即深度研究任意话题
- `/trends` - 当前热点列表（按评分排序）
- `/create` - 主动创建内容
- `/queue` - 待发布草稿队列
- `/log` - 快捷录入今日数据
- `/report` - 查看复盘报告
- `/strategy` - 查看当前内容策略
- `/settings` - 自动化开关面板
- `/llm` - LLM 供应商切换

**Inline 按钮交互**:
- 生成 A 类/B 类内容
- 生成评论
- 一键复制
- OpenClaw 自动发布
- 重新生成

### 5. 自动化设置

**可配置项**:
- **智能评论**: 开关 + 每日上限（默认 15 条，建议≤30）
- **自动点赞**: 开关 + 每日上限（默认 30 次）
- **自动 RT**: 开关 + 每日上限（默认 10 次）
- **自动发帖**: 开关（需配合 OpenClaw）

**LLM 供应商切换**:
支持 7 个供应商，通过 `/llm` 命令一键切换：
- Anthropic (Claude 3.5 Sonnet)
- OpenAI (GPT-4)
- Groq (Llama)
- Gemini (Google)
- OpenRouter (多模型聚合)
- NVIDIA NIM
- Ollama (本地部署)

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Telegram Bot Token ([获取教程](https://core.telegram.org/bots))
- Supabase 账号 ([免费创建](https://supabase.com))
- 至少一个 LLM 供应商 API Key

### 1. 克隆项目

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent-v2
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入必要配置
nano .env
```

**必要配置项**:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# LLM 供应商（至少配置一个）
ANTHROPIC_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
GROQ_API_KEY=gsk_xxx

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# OpenClaw（可选）
OPENCLAW_API_ENDPOINT=http://localhost:8080
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

在 Supabase 中执行 SQL 迁移脚本：

```bash
# 方法 1: 使用提供的 SQL 文件
psql -h $SUPABASE_URL -U postgres -d postgres -f migrations/001_initial_schema.sql

# 方法 2: 在 Supabase Dashboard 手动执行 SQL
```

**数据库表结构**:
- `trends` - 热点记录
- `content_queue` - 内容草稿
- `daily_log` - 每日记录
- `niche` - Niche 配置
- `automation_settings` - 自动化设置
- `strategy` - 策略版本

### 5. 运行系统

```bash
# 开发模式
python main.py

# 生产模式 (使用 PM2)
pm2 start main.py --name x-agent-v2 --interpreter python3
pm2 save && pm2 startup
```

---

## 📁 项目结构

```
x-agent-v2/
├── main.py                  # 应用入口 ✅
├── config.py                # 配置加载 ✅
├── .env                     # 环境变量
├── .env.example             # 配置模板
├── requirements.txt         # Python 依赖
│
├── modules/                 # 核心模块 ✅
│   ├── config.py            # 配置管理 (92/100)
│   ├── database.py          # Supabase 操作 (90/100)
│   ├── llm_router.py        # LLM 路由 (88/100)
│   ├── generator.py         # 内容生成 (90/100)
│   ├── scorer.py            # 热点评分 (92/100)
│   ├── research.py          # 数据采集 (88/100)
│   ├── trends.py            # 趋势采集 (85/100)
│   ├── bot.py               # Telegram Bot (90/100)
│   ├── openclaw_bridge.py   # OpenClaw 集成 (88/100)
│   └── scheduler.py         # 定时任务 (90/100)
│
├── prompts/                 # Prompt 模板 ✅
│   ├── type_a.txt           # A 类推文
│   ├── type_b.txt           # B 类视频脚本
│   ├── comment.txt          # 智能评论
│   └── review.txt           # 每日复盘
│
├── niche_voices/            # Niche 语气文件 ✅
│   ├── adult.txt            # 成人用品
│   ├── ai_tools.txt         # AI 工具
│   ├── beauty.txt           # 美妆
│   ├── crypto.txt           # 加密货币
│   ├── fitness.txt          # 健身
│   ├── humor.txt            # 搞笑
│   └── custom.txt           # 自定义
│
├── migrations/              # 数据库迁移 ✅
│   └── 001_initial_schema.sql
├── tests/                   # 测试用例 ✅
│   └── test_modules.py
└── data/                    # 本地缓存
```

---

## ⏰ 发布时机策略

| 时间段 | 内容类型 | 原因 |
|--------|---------|------|
| 07:30–09:00 | 资讯/数据类 A 类 | 通勤刷手机 |
| 12:00–13:00 | 投票/互动类 | 午休 |
| 19:00–21:00 | 推荐/Cheeky 类 | 全天最高在线峰值 |
| 21:30–23:00 | 感性/关系话题 | 睡前情绪高 |

**起步期节奏**（0-1k 粉丝）:
- 每天发 **3–5 条**（A:B = 2:1）
- 每天智能评论 **10–15 条**
- 每周至少 1 条互动投票
- 避开：周一早上、UK 公众假日白天

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **语言** | Python 3.11+ |
| **Bot 框架** | python-telegram-bot |
| **LLM** | Anthropic / OpenAI / Groq / Gemini / OpenRouter / NVIDIA NIM / Ollama |
| **数据库** | Supabase (PostgreSQL) |
| **数据采集** | last30days-skill, PRAW, pytrends |
| **自动化** | OpenClaw (Playwright stealth) |
| **调度** | APScheduler |
| **部署** | Mac 本地常驻 + PM2 |

---

## 📊 代码质量

**总体评分**: 90/100  
**完整度**: 95%  
**审查报告**: [CODE_REVIEW_COMPLETE.md](CODE_REVIEW_COMPLETE.md)

| 模块 | 评分 | 状态 |
|------|------|------|
| config.py | 92/100 | ✅ |
| database.py | 90/100 | ✅ |
| llm_router.py | 88/100 | ✅ |
| generator.py | 90/100 | ✅ |
| scorer.py | 92/100 | ✅ |
| research.py | 88/100 | ✅ |
| trends.py | 85/100 | ✅ |
| bot.py | 90/100 | ✅ |
| openclaw_bridge.py | 88/100 | ✅ |
| scheduler.py | 90/100 | ✅ |
| main.py | 92/100 | ✅ |

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行单个模块测试
pytest tests/test_modules.py -v

# 覆盖率报告
pytest --cov=modules --cov-report=html
```

---

## 📝 相关文档

- [完整代码审查报告](CODE_REVIEW_COMPLETE.md)
- [部署指南](DEPLOYMENT.md)
- [开发计划](../群聊记录/2026-03-24%20X 智能运营 Agent v2.0 开发计划.md)
- [OpenClaw 文档](https://docs.openclaw.ai)

---

## ⚠️ 注意事项

1. **API 限制**: 请遵守各平台的 API 使用限制和反爬虫政策
2. **账号安全**: 自动化工具可能违反平台服务条款，请谨慎使用
3. **内容审核**: AI 生成内容可能存在错误，发布前请人工审核
4. **数据隐私**: 请妥善保管 API Key 和敏感信息

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**Managed by Friday (CEO Agent)** 🐉  
**版本**: 2.0.0  
**状态**: 生产就绪 ✅  
**最后更新**: 2026-03-24

*X-Agent v2.0 - 让内容创作更简单*
