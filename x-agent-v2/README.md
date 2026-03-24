# X 智能运营 Agent v2.0

**多 Niche 内容自动化系统** - Telegram + OpenClaw 驱动

[![Status](https://img.shields.io/badge/status-complete-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Progress](https://img.shields.io/badge/progress-100%25-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Score](https://img.shields.io/badge/code%20score-90/100-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/sheldon010507-collab/x-agent)

---

## 🎯 项目简介

X智能运营Agent是一个为**任意Niche**（英语市场为主）构建的智能内容运营系统。通过Telegram Bot实现热点监控、智能内容生成、自动化评论和每日复盘，帮助运营者把每天找热点、写文案、刷评论的时间压缩到最低，专注高质量内容制作和账号私域转化。

---

## ✨ 核心功能

### 🔥 热点监控
- **多平台采集**: X Trending + Reddit + Google Trends
- **复合评分**: Relevance(40%) + Velocity(30%) + Authority(15%) + Convergence(15%)
- **智能分级**: ≥80分立即推送，60-79分存库，<60分丢弃

### 🤖 智能生成
- **A类 - AI全自动推文**: 3条备选，5种角度（Hot take/Data/互动投票/产品推荐/Cheeky）
- **B类 - 30秒视频脚本**: 含分镜建议和发布时间建议
- **C类 - 智能评论**: 带emoji + 问题结尾，提升回复率

### 🎭 Niche语气注入
支持7种专属语气，切换Niche时自动注入所有生成内容：

| Niche | 语气风格 | 典型句式 |
|-------|----------|----------|
| adult | cheeky, 暗示, 感性 | "you deserve this 😏" |
| ai_tools | 极客, 效率, 前沿 | "unpopular opinion:" |
| beauty | 种草, 姐妹情, 精致 | "girlies this is worth every penny 💅" |
| fitness | 励志, 数据, 挑战 | "no excuses. day X of Y ✅" |
| crypto | FOMO, alpha, 社群 | "not financial advice but..." |
| humor | 无厘头, 自黑, meme | "me: *does thing* also me:" |
| custom | 完全可编辑 | 用户自定义 |

### ⚙️ 自动化功能
- **定时热点采集**: 每2小时自动采集
- **自动智能评论**: 可设每日上限（默认15条）
- **每日复盘报告**: 21:00 UK时间自动生成
- **点赞/RT开关**: 可独立控制，各有每日上限

### 📊 数据驱动
- **Supabase云数据库**: PostgreSQL，完整数据追踪
- **5张数据表**: trends, content_queue, daily_log, strategy, automation_settings
- **策略版本管理**: 记录每次策略调整

---

## 🏗️ 项目结构

```
x-agent-v2/
├── main.py                    # 入口文件
├── requirements.txt           # Python依赖
├── .env.example              # 环境变量模板
├── .gitignore                # Git忽略配置
├── LICENSE                   # MIT开源协议
│
├── modules/                  # 核心模块（全部完成）
│   ├── config.py             # 配置管理
│   ├── database.py           # Supabase操作
│   ├── llm_router.py         # LLM多供应商路由
│   ├── generator.py          # 内容生成（A/B/C类）
│   ├── scorer.py             # 复合评分系统
│   ├── research.py           # 多平台数据采集
│   ├── trends.py             # 趋势采集（Reddit/Google/X）
│   ├── bot.py                # Telegram Bot
│   ├── openclaw_bridge.py    # OpenClaw集成
│   └── scheduler.py          # 定时任务调度
│
├── prompts/                  # Prompt模板
│   ├── type_a.txt            # A类推文模板
│   ├── type_b.txt            # B类视频脚本模板
│   ├── comment.txt           # 智能评论模板
│   └── review.txt            # 每日复盘模板
│
├── niche_voices/             # Niche语气文件
│   ├── adult.txt             # 成人用品
│   ├── ai_tools.txt          # AI工具
│   ├── beauty.txt            # 美妆
│   ├── fitness.txt           # 健身
│   ├── crypto.txt            # 加密货币
│   ├── humor.txt             # 搞笑
│   └── custom.txt            # 自定义
│
├── migrations/               # 数据库迁移
│   └── 001_initial_schema.sql
│
├── tests/                    # 单元测试
│   └── test_modules.py
│
└── DEPLOYMENT.md             # 部署指南
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
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

**必需配置**:
- `TELEGRAM_BOT_TOKEN` - Telegram Bot Token
- `SUPABASE_URL` - Supabase项目URL
- `SUPABASE_KEY` - Supabase服务端Key
- 至少一个LLM API Key

**可选配置**:
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - Reddit API
- `LLM_PROVIDER` - 默认LLM供应商（anthropic）
- `TIMEZONE` - 时区（Europe/London）

### 4️⃣ 初始化数据库

在Supabase SQL编辑器中执行 `migrations/001_initial_schema.sql`

### 5️⃣ 运行

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
| **LLM** | Anthropic / OpenAI / Groq / Gemini / OpenRouter / NVIDIA NIM / Ollama |
| **数据采集** | PRAW (Reddit) + pytrends + Nitter |
| **调度** | APScheduler |
| **自动化** | OpenClaw |

---

## 📊 项目状态

### 完成度: 100% ✅

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
| scheduler.py | 88/100 | ✅ |
| main.py | 92/100 | ✅ |

**平均评分**: 90/100

---

## 🔒 安全说明

- ✅ 所有API Key从环境变量读取，不硬编码
- ✅ 使用Supabase ORM，参数化查询防SQL注入
- ✅ Telegram Bot输入验证
- ✅ 每日上限控制防止滥用
- ✅ 随机延迟防检测

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

---

## 📞 支持

- **Issues**: [GitHub Issues](https://github.com/sheldon010507-collab/x-agent/issues)
- **部署指南**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**代码审查**: Sage (Reviewer Agent) ✅

**最后更新**: 2026-03-24
