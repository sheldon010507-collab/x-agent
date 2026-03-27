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

- 🔥 **多平台热点监控**：X + Reddit + Google Trends + last30days 混合检索
- 🤖 **AI 内容生成**：推文(A类) / 视频脚本(B类) / 智能评论(C类)
- 🎭 **7 种 Niche 语气**：成人用品、AI工具、美妆、健身、加密、搞笑、自定义
- ⚡ **完整防封机制**：随机延迟(10-40秒)、内容变体、每日上限控制
- 🤖 **Telegram Bot 驱动**：/start /set_niche /research /create /score 等完整命令
- 📊 **Supabase 持久化**：热点记录 + 内容草稿 + 每日复盘

**检索方式**：不依赖官方 X API，采用 OpenClaw + last30days 混合方案，成本低、数据真实。

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
| `research.py` | 多平台研究 + last30days 集成 |
| `scorer.py` | 四维评分系统 (Relevance + Velocity + Authority + Convergence) |
| `generator.py` | A/B/C 类内容生成 |
| `openclaw_bridge.py` | OpenClaw 自动化 + 防封机制 |
| `llm_router.py` | 多 LLM 路由 (Claude/Groq/OpenAI) |
| `database.py` | Supabase 数据持久化 |

---

## ⚠️ 风险声明

**本项目仅供学习研究使用。**

- 自动化操作 X (Twitter) 存在账号风险，请谨慎使用
- 建议使用小号测试，不要用于主账号
- 作者不对任何账号封禁负责
- 请遵守 X 平台服务条款

---

## 📄 License

MIT License - 欢迎 Fork、Star、PR！

---

**Star ⭐ 支持一下～ 感谢每一位贡献者！**
