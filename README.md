# X-Agent v0 Final

> ⚠️ **风险声明 / Risk Disclaimer**
>
> 本工具仅供学习和研究用途。使用本工具进行自动化操作可能违反平台服务条款。
> 作者不对因使用本工具导致的任何账号封禁、数据损失或其他后果负责。
>
> This tool is for learning and research purposes only. Automated operations may violate platform Terms of Service.
> The author is not responsible for any account bans, data loss, or other consequences.

**X（Twitter）智能运营Agent**
热点监控 + AI内容生产 + OpenClaw自动发帖/评论 + 每日复盘

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-v0_Final-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 核心亮点

- 🔥 **多平台热点监控**：Reddit + Hacker News + Google Trends 原生异步采集
- 🤖 **AI 内容生成**：推文(A类) / 视频脚本(B类) / 智能评论(C类)
- 🎭 **7 种 Niche 语气**：成人用品、AI工具、美妆、健身、加密、搞笑、自定义
- ⚡ **完整防封机制**：随机延迟(10-40秒)、内容变体、每日上限控制
- ✅ **强制人工审核**：所有内容都需经过二次确认，无自动发布路径
- 🤖 **Telegram Bot 驱动**：/start /set_niche /research /create /score 等完整命令
- 📊 **Supabase 持久化**：热点记录 + 内容草稿 + 每日复盘

**检索方式**：不依赖官方 X API，采用原生异步 Python 实现（PRAW、aiohttp、pytrends）+ OpenClaw 自动化方案，成本低、数据真实。

---

## 3分钟上手

见 [x-agent/docs/UP_AND_RUNNING.md](x-agent/docs/UP_AND_RUNNING.md)

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 Telegram Bot Token
python main.py
```

---

## 仓库结构

```
x-agent/
├── archive/           # 历史版本归档
│   ├── x-agent/       # v1
│   └── x-agent-v2/    # v2
└── x-agent/           # 当前版本 (v0 Final)
    ├── modules/       # 核心模块
    ├── niche_voices/  # 7种语气模板
    ├── prompts/       # Prompt模板
    ├── tests/         # 测试文件
    ├── docs/          # 文档
    └── migrations/    # 数据库迁移
```

---

## 核心模块

| 模块 | 功能 |
|------|------|
| `research.py` | 多平台研究（Reddit/HN/Google Trends 原生异步采集）|
| `scorer.py` | 四维评分系统 (Relevance + Velocity + Authority + Convergence) |
| `generator.py` | A/B/C 类内容生成 + 风险评分 |
| `bot.py` | Telegram Bot 驱动 + 强制人工二次确认 |
| `openclaw_bridge.py` | OpenClaw 自动化 + 防封机制 |
| `llm_router.py` | 多 LLM 路由 (Claude/Groq/OpenAI) |
| `database.py` | Supabase 数据持久化 |

---

## 审批工作流

X-Agent **强制所有内容都经过人工确认**，确保操作的安全性和可控性：

1. **内容生成**：通过 `/create` 命令生成 A/B/C 类内容
2. **风险评估**：系统自动计算 Risk Score（0-100），显示风险等级
3. **一次确认**：用户点击「✅ 人工确认发布」按钮
4. **二次确认**：弹出「确认无误，发布？」对话框，防止误操作
5. **手动发布**：用户前往 X（Twitter）手动发布内容
6. **数据记录**：使用 `/log post 1` 记录已发布的内容

**关键特性**：
- ✅ 无自动发布路径，即使 Risk Score < 70
- ✅ 二次确认机制防止误操作
- ✅ 用户对发布内容保持完全控制
- ✅ 所有操作都可回溯

---

## ⚠️ 风险声明

**本项目仅供学习研究使用。**

- 自动化操作 X (Twitter) 存在账号风险，请谨慎使用
- 建议使用小号测试，不要用于主账号
- 作者不对任何账号封禁负责
- 请遵守 X 平台服务条款
- **重要**：本项目所有内容生成都需人工审核后才能发布，用户对发布内容负责

---

## 📄 License

MIT License - 欢迎 Fork、Star、PR！

---

**Star ⭐ 支持一下～ 感谢每一位贡献者！**
