# X-Agent v3.0

**智能 X (Twitter) 内容运营自动化系统**

[![Version](https://img.shields.io/badge/version-3.0.0-blue)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](https://opensource.org/licenses/MIT)

---

## 📖 项目介绍

X-Agent v3.0 是一个智能化的 X (Twitter) 内容运营自动化系统，专为多 Niche 内容创作者设计。通过 AI 驱动的热点采集、智能评分、内容生成和自动发布，帮助你高效运营多个垂直领域账号。

### ✨ 核心功能

- **🔥 智能热点采集**: 多平台实时监控，4 维复合评分（Relevance, Velocity, Authority, Convergence）
- **🤖 AI 内容生成**: 支持 A/B/C 三类内容创作，7 种 Niche 语气切换
- **🌐 多 LLM 供应商**: 支持 7 个 LLM 供应商（Anthropic, OpenAI, Groq, Gemini, OpenRouter, NVIDIA NIM, Ollama）
- **📱 Telegram Bot**: 完整的命令行和 Inline 按钮交互
- **🔗 OpenClaw 集成**: 自动化发布到 X，防封机制完善
- **📊 数据持久化**: Supabase 数据库支持，完整的内容队列和日志系统
- **⏰ 定时任务**: 自动热点采集、每日复盘、自动评论

### 🎯 适用场景

- 多账号运营者（MCN 机构、营销团队）
- 垂直领域内容创作者
- 需要自动化发布的工作流
- 想减少重复性运营工作的个人

---

## 🚀 快速开始（3 步启动）

### 步骤 1: 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd x-agent-v3

# 安装 Python 依赖
pip3 install -r requirements.txt --break-system-packages
```

### 步骤 2: 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入必要配置
# 必填项：TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY, 至少一个 LLM API Key
```

### 步骤 3: 启动应用

```bash
# 启动主程序
python3 main.py
```

启动成功后会显示：
```
🚀 Initializing X-Agent v3.0...
✅ Config loaded (LLM: anthropic)
✅ Database initialized
✅ LLM Router initialized (Provider: anthropic)
✅ Content Generator initialized (Niche: general)
✅ Telegram Bot initialized
✅ Scheduler initialized
🎉 All components initialized successfully!
```

---

## ⚙️ 配置说明

### 环境变量 (.env)

所有配置项说明见 **[CONFIG.md](CONFIG.md)** 或下方详细章节。

快速配置清单：

| 配置项 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram Bot Token | `123456:ABC-DEF1234...` |
| `TELEGRAM_CHAT_ID` | ✅ | 管理员聊天 ID | `-1001234567890` |
| `SUPABASE_URL` | ✅ | Supabase 项目 URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | Supabase API Key | `eyJ...` |
| `ANTHROPIC_API_KEY` | ✅* | Anthropic API Key | `sk-ant-...` |
| `LLM_PROVIDER` | ❌ | 默认 LLM 供应商 | `anthropic` |
| `LLM_MODEL` | ❌ | 默认模型 | `claude-3-5-sonnet-20241022` |

*至少需要配置一个 LLM 供应商的 API Key

---

## 🎨 Niche 切换教程

X-Agent 支持 7 种内置 Niche（垂直领域），每种 Niche 有独特的语料库和表达风格。

### 可用 Niche 列表

| Niche ID | 名称 | 说明 |
|----------|------|------|
| `adult` | 成人用品 | 健康、亲密关系相关 |
| `ai_tools` | AI 工具 | 人工智能、效率工具 |
| `beauty` | 美妆 | 护肤、彩妆、美容 |
| `fitness` | 健身 | 运动、减脂、增肌 |
| `crypto` | 加密货币 | 区块链、DeFi、NFT |
| `humor` | 搞笑 | 段子、梗、幽默内容 |
| `general` | 通用 | 默认 Niche，适合综合内容 |
| `custom` | 自定义 | 用户自定义语料 |

### 切换方法

#### 方法 1: Telegram Bot 命令

在 Bot 中发送 `/set_niche`，通过 Inline 按钮选择 Niche。

#### 方法 2: 代码中切换

```python
from config import config

# 切换到 AI 工具 Niche
config.set_niche('ai_tools')

# 获取当前 Niche
current = config.niche.current_niche
```

### 自定义 Niche 语料

编辑 `niche_voices/custom.txt` 文件，添加你的专属语料：

```text
# custom.txt 示例
今天也要加油鸭！
生活不易，全靠演技
打工人，打工魂，打工都是人上人
```

---

## 🤖 LLM 供应商配置教程

X-Agent 支持 7 个 LLM 供应商，可动态切换。

### 支持的供应商

| 供应商 | Provider | 默认模型 | 特点 |
|--------|----------|----------|------|
| Anthropic | `anthropic` | claude-3-5-sonnet-20241022 | 高质量，适合长文本 |
| OpenAI | `openai` | gpt-4o | 通用性强 |
| Groq | `groq` | llama-3.3-70b-versatile | 速度快，免费额度高 |
| Gemini | `gemini` | gemini-2.0-flash-exp | 多模态支持 |
| OpenRouter | `openrouter` | anthropic/claude-3.5-sonnet | 聚合多个模型 |
| NVIDIA NIM | `nvidia` | meta/llama-3.1-405b-instruct | 企业级，高性能 |
| Ollama | `ollama` | llama3.2 | 本地部署，隐私安全 |

### 配置示例

```bash
# .env 配置多个供应商
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GROQ_API_KEY=gsk_xxx
GEMINI_API_KEY=xxx
OPENROUTER_API_KEY=xxx
NVIDIA_NIM_API_KEY=xxx

# 默认使用 Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

### 动态切换供应商

在 Telegram Bot 中使用 `/llm` 命令，通过 Inline 按钮切换。

---

## 📚 详细配置说明

完整配置说明见 **[CONFIG.md](CONFIG.md)**，包括：

- `.env.example` 每个字段详细说明
- 如何获取 Telegram Bot Token（附 BotFather 教程链接）
- 如何获取 Supabase 配置
- 各 LLM 供应商 API Key 获取方式
- OpenClaw 安装和配置指南

---

## 🤖 Bot 命令列表

| 命令 | 说明 |
|------|------|
| `/start` | 欢迎信息和今日热点概览 |
| `/help` | 帮助文档 |
| `/set_niche` | 切换 Niche |
| `/research` | 深度研究话题 |
| `/trends` | 热点列表 |
| `/create` | 创建内容 |
| `/log` | 快捷录入数据 |
| `/report` | 复盘报告 |
| `/strategy` | 查看策略 |
| `/settings` | 自动化设置 |
| `/llm` | LLM 供应商切换 |

---

## ❓ 常见问题解答 (FAQ)

### Q1: 启动时报 "缺少必要配置" 错误？

**A**: 检查 `.env` 文件中是否填写了必填项：
- `TELEGRAM_BOT_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- 至少一个 LLM 供应商的 API Key

### Q2: 如何获取 Telegram Bot Token？

**A**: 
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建新 Bot
3. 按提示设置 Bot 名称和用户名
4. BotFather 会返回 Token，格式如 `123456:ABC-DEF1234...`
5. 将 Token 填入 `.env` 的 `TELEGRAM_BOT_TOKEN`

详细教程见 [CONFIG.md](CONFIG.md)。

### Q3: Supabase 如何配置？

**A**:
1. 访问 [supabase.com](https://supabase.com) 注册账号
2. 创建新项目，记录项目 URL 和 API Key
3. 在项目 SQL 编辑器中运行 `migrations/001_initial_schema.sql`
4. 将 URL 和 Key 填入 `.env`

详细步骤见 [CONFIG.md](CONFIG.md)。

### Q4: 如何切换 LLM 供应商？

**A**: 在 Bot 中使用 `/llm` 命令，通过 Inline 按钮选择供应商。或修改 `.env` 中的 `LLM_PROVIDER` 后重启应用。

### Q5: OpenClaw 是什么？必须配置吗？

**A**: OpenClaw 是 X (Twitter) 自动化发布工具，用于将生成的内容自动发布到 X。如果只需要生成内容而不自动发布，可以不配置 OpenClaw。

### Q6: 测试环境如何搭建？

**A**:
1. 使用 `OLLAMA_BASE_URL=http://localhost:11434` 配置本地 Ollama
2. 安装 Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
3. 拉取模型：`ollama pull llama3.2`
4. 设置 `LLM_PROVIDER=ollama`

### Q7: 如何查看日志？

**A**: 应用日志输出在终端，也可以使用 `/log` 命令在 Bot 中查看操作日志。

---

## 🛠️ 部署指南

详细部署步骤见 **[DEPLOYMENT.md](DEPLOYMENT.md)**，包括：

- Mac/Windows/Linux 部署步骤
- pm2 常驻配置
- Docker 部署方案
- 生产环境建议

快速部署（生产环境）：

```bash
# 使用 pm2 常驻
pm2 start main.py --name x-agent-v3 --interpreter python3

# 开机自启
pm2 save
pm2 startup
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发环境搭建

```bash
# 克隆项目
git clone <repository-url>
cd x-agent-v3

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
python3 tests/test_core_modules.py
```

### 提交代码

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

- 遵循 PEP 8 规范
- 添加完整的类型注解
- 所有类和方法必须有文档字符串
- 核心功能必须编写测试用例

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw) - X 自动化工具
- [Supabase](https://supabase.com) - 数据库支持
- [APScheduler](https://apscheduler.readthedocs.io) - 定时任务调度
- [python-telegram-bot](https://python-telegram-bot.org) - Telegram Bot 框架

---

## 📬 联系方式

- 项目主页：[GitHub](https://github.com)
- 问题反馈：[Issues](https://github.com/issues)
- 讨论区：[Discussions](https://github.com/discussions)

---

**最后更新**: 2026-03-25  
**版本**: v3.0.0  
**维护者**: Friday (CEO Agent) 🐉
