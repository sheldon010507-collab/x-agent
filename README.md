# X-Agent v3.0

<div align="center">

**AI-Powered X (Twitter) Operations Agent**

*Crave it. Research it. Post it.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/yourusername/x-agent.svg?style=social)](https://github.com/yourusername/x-agent/stargazers)

[English](#english) | [中文](#中文)

</div>

---

<a name="english"></a>
## English

### Features

- 🔍 **Multi-Platform Research** - Deep integration with last30days-skill for 8+ platform data collection (X, Reddit, YouTube, TikTok, Hacker News, Web)
- 🎯 **4-Dimensional Scoring** - Relevance, Velocity, Authority, Convergence scoring system
- 🎭 **7 Pre-built Niches** - Adult UK, AI Tools, Beauty, Fitness, Crypto, Humor, Custom
- 🤖 **Multi-LLM Support** - OpenAI, Anthropic, Gemini, DeepSeek, Moonshot, Qwen, Zhipu
- 🛡️ **Anti-Ban System** - Random delays, content variants, daily limits for safe automation
- 📱 **Telegram Bot** - Full control via Telegram commands
- 📊 **Supabase Backend** - Cloud database with real-time sync

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/x-agent.git
cd x-agent

# 2. Install dependencies
pip install -r x-agent/requirements.txt

# 3. Configure environment
cp x-agent/.env.example x-agent/.env
# Edit .env with your API keys

# 4. Run
python x-agent/main.py
```

See [UP_AND_RUNNING.md](./docs/UP_AND_RUNNING.md) for detailed setup guide.

### Supported Niches

| Command | Niche |
|---------|-------|
| `/set_niche adult_uk` | Adult Products (UK Market) |
| `/set_niche ai_tools` | AI Tool Reviews |
| `/set_niche beauty` | Beauty & Skincare |
| `/set_niche fitness` | Health & Fitness |
| `/set_niche crypto` | Cryptocurrency |
| `/set_niche humor` | Humor & Memes |
| `/set_niche custom` | Custom Mode |

### Architecture

```
x-agent/
├── modules/
│   ├── research.py      # Multi-platform research (last30days)
│   ├── scorer.py        # 4D scoring system
│   ├── generator.py     # A/B/C content generation
│   ├── llm_router.py    # Multi-LLM routing
│   ├── openclaw_bridge.py  # Anti-ban automation
│   ├── bot.py           # Telegram Bot
│   └── scheduler.py     # Task scheduling
├── prompts/             # Content templates
├── niche_voices/        # Niche-specific tones
└── migrations/          # Database schema
```

---

<a name="中文"></a>
## 中文

### 功能特性

- 🔍 **多平台研究** - 深度集成 last30days-skill，支持 8+ 平台数据采集（X、Reddit、YouTube、TikTok、Hacker News、Web）
- 🎯 **四维评分系统** - 相关度、增速、权威度、汇聚度复合评分
- 🎭 **7 种预置领域** - 成人用品、AI 工具、美妆、健身、加密货币、幽默、自定义
- 🤖 **多模型支持** - OpenAI、Anthropic、Gemini、DeepSeek、Moonshot、Qwen、Zhipu
- 🛡️ **防封机制** - 随机延迟、内容变体、每日上限
- 📱 **Telegram Bot** - 完整的 Telegram 命令控制
- 📊 **Supabase 后端** - 云数据库实时同步

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/x-agent.git
cd x-agent

# 2. 安装依赖
pip install -r x-agent/requirements.txt

# 3. 配置环境
cp x-agent/.env.example x-agent/.env
# 编辑 .env 填入 API 密钥

# 4. 运行
python x-agent/main.py
```

详细设置请参考 [UP_AND_RUNNING.md](./docs/UP_AND_RUNNING.md)。

### 支持的领域

| 命令 | 领域 |
|-----|-----|
| `/set_niche adult_uk` | 成人用品（英国市场）|
| `/set_niche ai_tools` | AI 工具评测 |
| `/set_niche beauty` | 美妆护肤 |
| `/set_niche fitness` | 健身健康 |
| `/set_niche crypto` | 加密货币 |
| `/set_niche humor` | 幽默段子 |
| `/set_niche custom` | 自定义模式 |

### 架构

```
x-agent/
├── modules/
│   ├── research.py      # 多平台研究（last30days）
│   ├── scorer.py        # 四维评分系统
│   ├── generator.py     # A/B/C 内容生成
│   ├── llm_router.py    # 多模型路由
│   ├── openclaw_bridge.py  # 防封自动化
│   ├── bot.py           # Telegram Bot
│   └── scheduler.py     # 任务调度
├── prompts/             # 内容模板
├── niche_voices/        # 领域语气
└── migrations/          # 数据库 Schema
```

---

## Documentation

- [UP_AND_RUNNING.md](./docs/UP_AND_RUNNING.md) - 5分钟上手指南
- [CHANGELOG.md](./docs/CHANGELOG.md) - 版本变更记录
- [DEPLOYMENT.md](./docs/DEPLOYMENT.md) - 生产部署指南
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 贡献指南

## License

[MIT License](./LICENSE)

## Star History

<a href="https://www.star-history.com/#yourusername/x-agent&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=yourusername/x-agent&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=yourusername/x-agent&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=yourusername/x-agent&type=Date" />
 </picture>
</a>
