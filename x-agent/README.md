# X-Agent v0 Final

**X（Twitter）智能运营Agent**
热点监控 + AI内容生产 + OpenClaw自动发帖/评论 + 每日复盘

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-v0_Final-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 核心功能

### 🔥 热点监控
- 多平台数据源：X (Twitter)、Reddit、Google Trends
- last30days-skill 深度集成（可选增强）
- 四维评分系统筛选高价值话题

### 🤖 AI 内容生成
- **A 类**：全自动推文（3条备选）
- **B 类**：视频脚本（需人工拍摄）
- **C 类**：智能评论（带上下文）

### 🎭 Niche Voices
预置 7 种语气风格：

| Niche | 文件 |
|-------|------|
| 成人用品（英国）| `adult_uk.md` |
| AI 工具 | `ai_tools.md` |
| 美妆护肤 | `beauty.md` |
| 健身健康 | `fitness.md` |
| 加密货币 | `crypto.md` |
| 幽默段子 | `humor.md` |
| 自定义模板 | `custom.md` |

### ⚡ 防封机制
- 随机延迟：10-40 秒
- 内容变体：emoji/句式随机
- 每日上限：可配置（默认评论15条/天）
- 时段模拟：真实用户活跃时段

---

## 快速开始

### 1. 克隆并安装
```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env，填入：
# - TELEGRAM_BOT_TOKEN（必填）
# - LLM API Key（至少一个）
# - Supabase 配置（可选）
```

### 3. 运行
```bash
python main.py
```

### 4. Telegram Bot 命令
```
/start      - 显示今日热点 + 快捷菜单
/set_niche  - 切换 Niche 语气
/research   - 立即研究当前话题
/create     - 生成 A/B/C 类内容
/score      - 查看四维评分详情
/trends     - 热点概览
/log        - 录入今日数据
/report     - 每日复盘报告
/settings   - 当前配置
```

---

## 项目结构

```
x-agent/
├── main.py              # 入口文件
├── config.py            # 配置管理
├── bot.py               # Telegram Bot
├── modules/
│   ├── research.py      # 热点研究
│   ├── scorer.py        # 四维评分
│   ├── generator.py     # 内容生成
│   ├── openclaw_bridge.py  # OpenClaw 集成
│   ├── llm_router.py    # LLM 路由
│   └── database.py      # 数据持久化
├── niche_voices/        # 语气模板
├── prompts/             # Prompt 模板
├── tests/               # 测试文件
├── docs/                # 文档
└── migrations/          # 数据库迁移
```

---

## 四维评分系统

每个热点按以下维度评分（满分 100）：

| 维度 | 权重 | 说明 |
|------|------|------|
| Relevance | 40% | 与 Niche 相关度 |
| Velocity | 30% | 传播速度 |
| Authority | 15% | 来源权威性 |
| Convergence | 15% | 多平台共振 |

**推送策略**：
- ≥80 分：立即 Telegram 推送 + 自动生成评论
- 60-79 分：存库，每日 21:00 汇总展示
- <60 分：自动丢弃

---

## 配置说明

主要配置项见 `.env.example`：

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# LLM（至少配置一个）
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GROQ_API_KEY=gsk_xxx

# 防封配置
MAX_COMMENTS_PER_DAY=15
DELAY_MIN=10
DELAY_MAX=40
```

---

## ⚠️ 风险声明

**本项目仅供学习研究使用。**

- 自动化操作 X (Twitter) 存在账号风险
- 建议使用小号测试
- 请遵守 X 平台服务条款
- 作者不对任何账号封禁负责

---

## 更新日志

详见 [docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## License

MIT License
