# X-Agent v3.0 — 通用智能运营 Agent

> **多平台热点采集 + AI 内容生成 + Telegram 自动化运营**

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Features

- 🔍 **Multi-platform Research** — X, Reddit, YouTube, Hacker News, Web, TikTok, Instagram, Bluesky, Polymarket
- 🤖 **7 LLM Providers** — Anthropic, OpenAI, Groq, Gemini, OpenRouter, NVIDIA, Ollama
- 📊 **4-Dimension Scoring** — Relevance (40%) + Velocity (30%) + Authority (15%) + Convergence (15%)
- 🎯 **7 Niche Voices** — Adult UK, AI Tools, Beauty, Fitness, Crypto, Humor, Custom
- 📱 **Telegram Bot** — 11 commands + Inline buttons
- ⏰ **Auto Scheduling** — Collect every 2h, Daily review at 21:00
- 🛡️ **Anti-Ban** — Random delay + Content variants + Daily limits

### Quick Start

```bash
# 1. Clone
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Setup database
supabase db push

# 4. Install & Run
pip install -r requirements.txt
python main.py
```

See [UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md) for detailed setup.

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Show hot trends overview |
| `/trends` | View current trends |
| `/set_niche <name>` | Switch niche mode |
| `/generate_a` | Generate Type A tweet |
| `/generate_b` | Generate Type B video script |
| `/generate_c` | Generate smart comment |
| `/settings` | Open settings panel |

### Architecture

```
x-agent/
├── main.py           # Entry point
├── bot.py            # Telegram Bot (700+ lines)
├── config.py         # Config management
├── modules/
│   ├── database.py       # Supabase CRUD
│   ├── llm_router.py     # 7-provider routing
│   ├── research.py       # Multi-platform research
│   ├── scorer.py         # 4-dimension scoring
│   ├── generator.py      # A/B/C content generation
│   ├── openclaw_bridge.py # OpenClaw integration + anti-ban
│   └── scheduler.py      # Auto scheduling
├── prompts/          # Prompt templates
├── niche_voices/     # 7 tone files
└── migrations/       # Supabase schema
```

### Documentation

- [CONFIG.md](x-agent/CONFIG.md) — Configuration guide
- [DEPLOYMENT.md](x-agent/DEPLOYMENT.md) — Production deployment
- [UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md) — 5-min setup guide

---

<a name="中文"></a>
## 中文

### 功能特点

- 🔍 **多平台研究** — X、Reddit、YouTube、Hacker News、Web、TikTok、Instagram、Bluesky、Polymarket
- 🤖 **7 种 LLM 供应商** — Anthropic、OpenAI、Groq、Gemini、OpenRouter、NVIDIA、Ollama
- 📊 **4 维复合评分** — 相关性 (40%) + 增速 (30%) + 权威性 (15%) + 汇聚性 (15%)
- 🎯 **7 种 Niche 语气** — 成人用品、AI 工具、美妆、健身、加密货币、幽默、自定义
- 📱 **Telegram Bot** — 11 个命令 + Inline 按钮
- ⏰ **自动调度** — 每 2 小时采集 + 每日 21:00 复盘
- 🛡️ **防封机制** — 随机延迟 + 内容变体 + 每日限额

### 快速开始

```bash
# 1. 克隆
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent

# 2. 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 初始化数据库
supabase db push

# 4. 安装并运行
pip install -r requirements.txt
python main.py
```

详细步骤见 [UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md)。

### 命令列表

| 命令 | 说明 |
|------|------|
| `/start` | 显示热点概览 |
| `/trends` | 查看当前热点 |
| `/set_niche <name>` | 切换 Niche 模式 |
| `/generate_a` | 生成 A 类推文 |
| `/generate_b` | 生成 B 类视频脚本 |
| `/generate_c` | 生成智能评论 |
| `/settings` | 打开设置面板 |

### 目录结构

```
x-agent/
├── main.py           # 主入口
├── bot.py            # Telegram Bot (700+ 行)
├── config.py         # 配置管理
├── modules/          # 核心模块
│   ├── database.py       # Supabase CRUD
│   ├── llm_router.py     # 7 供应商路由
│   ├── research.py       # 多平台研究
│   ├── scorer.py         # 4 维评分
│   ├── generator.py      # A/B/C 内容生成
│   ├── openclaw_bridge.py # OpenClaw 集成 + 防封
│   └── scheduler.py      # 自动调度
├── prompts/          # Prompt 模板
├── niche_voices/     # 7 种语气文件
└── migrations/       # Supabase Schema
```

### 文档

- [CONFIG.md](x-agent/CONFIG.md) — 配置指南
- [DEPLOYMENT.md](x-agent/DEPLOYMENT.md) — 生产部署
- [UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md) — 5 分钟上手

---

## License

MIT License — See [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
