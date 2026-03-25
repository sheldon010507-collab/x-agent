# X-Agent v3.0

<div align="center">

**真正通用的 X (Twitter) 智能运营 Agent**

[![GitHub stars](https://img.shields.io/github/stars/sheldon010507-collab/x-agent?style=social)](https://github.com/sheldon010507-collab/x-agent/stargazers)
[![GitHub license](https://img.shields.io/github/license/sheldon010507-collab/x-agent)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

[English](#english) | [中文](#中文)

</div>

---

## English

### 🚀 Features

- **🔥 Hot Topic Monitoring**: Real-time monitoring across 8+ platforms (X/Reddit/YouTube/TikTok/IG/Bluesky/HN/Polymarket)
- **🤖 AI Content Generation**: Type A (tweets), Type B (video scripts), Type C (smart comments)
- **📊 Compound Scoring**: Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
- **🎭 Multi-Niche Support**: 7 built-in niches with one-click switching
- **🔒 Anti-Ban System**: Random delays + content variants + daily limits
- **📱 Telegram Bot**: 15+ commands with inline buttons

### 📦 Quick Start

```bash
# Clone repository
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run
python main.py
```

### 🎭 Supported Niches

| Niche | Voice Style | Example |
|-------|-------------|---------|
| `adult_uk` | Cheeky, suggestive | "Your body will thank you 😏" |
| `ai_tools` | Geeky, efficiency | "This changed my workflow ⚡" |
| `beauty` | Sisterly, authentic | "Girlies, you NEED this 💅" |
| `fitness` | Motivational, data-driven | "No excuses 💪" |
| `crypto` | Alpha, community | "Not financial advice but... 👀" |
| `humor` | Witty, self-deprecating | "Me: *does thing* Also me: 🤡" |
| `custom` | Fully customizable | Define your own voice |

### 🏗️ Architecture

```
x-agent/
├── main.py              # Entry point
├── modules/
│   ├── research.py      # last30days deep research
│   ├── scorer.py        # Compound scoring
│   ├── generator.py     # A/B/C content generation
│   ├── openclaw_bridge.py  # Anti-ban automation
│   └── bot.py           # Telegram Bot
├── prompts/             # Prompt templates
├── niche_voices/        # Voice files (.md)
└── tests/               # Unit tests
```

### ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `SUPABASE_URL` | ✅ | Supabase Project URL |
| `SUPABASE_KEY` | ✅ | Supabase API Key |
| `ANTHROPIC_API_KEY` | ⚪ | Claude API Key |
| `OPENAI_API_KEY` | ⚪ | OpenAI API Key |

> At least one LLM API key is required.

### 📖 Documentation

- [5-Minute Setup Guide](docs/UP_AND_RUNNING.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Changelog](docs/CHANGELOG.md)

---

## 中文

### 🚀 功能特性

- **🔥 热点监控**: 8+ 平台实时监控（X/Reddit/YouTube/TikTok/IG/Bluesky/HN/Polymarket）
- **🤖 AI 内容生成**: A类推文、B类视频脚本、C类智能评论
- **📊 复合评分**: Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
- **🎭 多 Niche 支持**: 7 种内置语气，一键切换
- **🔒 防封机制**: 随机延迟 + 内容变体 + 每日上限
- **📱 Telegram Bot**: 15+ 指令 + Inline 按钮

### 📦 快速开始

```bash
# 克隆仓库
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 运行
python main.py
```

### 🎭 支持的 Niche

| Niche | 语气风格 | 示例 |
|-------|---------|------|
| `adult_uk` | Cheeky、暗示 | "Your body will thank you 😏" |
| `ai_tools` | 极客、效率 | "This changed my workflow ⚡" |
| `beauty` | 种草、姐妹情 | "Girlies, you NEED this 💅" |
| `fitness` | 励志、数据驱动 | "No excuses 💪" |
| `crypto` | Alpha、社群 | "Not financial advice but... 👀" |
| `humor` | 无厘头、自黑 | "Me: *does thing* Also me: 🤡" |
| `custom` | 完全自定义 | 定义你自己的语气 |

### ⚙️ 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token |
| `SUPABASE_URL` | ✅ | Supabase 项目 URL |
| `SUPABASE_KEY` | ✅ | Supabase API Key |
| `ANTHROPIC_API_KEY` | ⚪ | Claude API Key |
| `OPENAI_API_KEY` | ⚪ | OpenAI API Key |

> 至少需要一个 LLM API Key。

### 📖 文档

- [5分钟上手指南](docs/UP_AND_RUNNING.md)
- [部署指南](docs/DEPLOYMENT.md)
- [更新日志](docs/CHANGELOG.md)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<div align="center">

**Made with ❤️ by the X-Agent Team**

[⬆ Back to Top](#x-agent-v30)

</div>
