# X-Agent v0

**X (Twitter) 热点监控 + 智能内容生产 + 自动复盘系统**

[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-0.0.0-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📖 简介

X-Agent 是一个**多 Niche 内容自动化运营系统**，基于 Telegram + OpenClaw 驱动，实现：

- 🔥 **热点监控**: 多平台采集（X + Reddit + Google Trends），复合评分筛选
- 🤖 **智能生成**: A 类推文 / B 类视频脚本 / C 类评论，AI 自动生成
- 🎭 **Niche 语气**: 7 种专属语气风格（成人用品、AI 工具、美妆、健身、加密、搞笑、自定义）
- ⚙️ **自动化**: 定时采集、自动评论、智能发布、每日复盘

**核心价值**: 把每天找热点、写文案、刷评论的时间压缩到最低，专注高质量 B 类内容制作和账号私域转化。

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

```bash
cp .env.example .env
# 编辑 .env 填入你的 API keys
```

### 4. 运行

```bash
python main.py
```

详细上手指南请参考 [docs/UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md)

---

## 📁 项目结构

```
x-agent/
├── modules/           # 核心模块
│   ├── research.py    # 热点采集与评分
│   ├── scorer.py      # 四维评分系统
│   ├── generator.py   # 内容生成引擎
│   ├── database.py    # 数据持久化
│   ├── openclaw_bridge.py  # OpenClaw 集成
│   └── llm_router.py  # LLM 路由
├── niche_voices/      # 语气模板（7种）
├── prompts/           # Prompt 模板
├── tests/             # 测试文件
├── docs/              # 文档
└── migrations/        # 数据库迁移
```

---

## 🎭 Niche Voices

预置 7 种语气风格：

| 文件 | Niche |
|------|-------|
| `adult_uk.md` | 成人用品（英国）|
| `ai_tools.md` | AI 工具 |
| `beauty.md` | 美妆护肤 |
| `fitness.md` | 健身健康 |
| `crypto.md` | 加密货币 |
| `humor.md` | 幽默段子 |
| `custom.md` | 自定义模板 |

---

## ⚡ 防封机制

X-Agent 内置完整的防封策略：

- **随机延迟**: 操作间隔 30-180 秒随机
- **内容变体**: 同一内容多种表达方式
- **每日上限**: 自动控制日操作量
- **时段模拟**: 模拟真实用户活跃时段

详见 [CODE_REVIEW_COMPLETE.md](CODE_REVIEW_COMPLETE.md)

---

## 📊 四维评分系统

每个热点按以下维度评分（满分 100）：

| 维度 | 权重 | 说明 |
|------|------|------|
| Relevance | 40% | 与 Niche 相关度 |
| Velocity | 30% | 传播速度 |
| Authority | 15% | 来源权威性 |
| Convergence | 15% | 多平台共振 |

---

## 🔧 配置

主要配置项见 `.env.example`：

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# LLM APIs
OPENAI_API_KEY=your_openai_key
X_URL_API_KEY=your_x_url_key

# Database
DATABASE_URL=sqlite:///x_agent.db
```

---

## 📝 更新日志

详见 [docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

详见 [CONTRIBUTING.md](../CONTRIBUTING.md)
