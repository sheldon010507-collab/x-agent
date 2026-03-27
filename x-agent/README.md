# X-Agent v0

**X (Twitter) 智能运营 Agent**  
热点监控 + AI 内容生产 + OpenClaw 自动发帖/评论 + 每日复盘

![Status](https://img.shields.io/badge/status-production--ready-green)
![Version](https://img.shields.io/badge/version-v0--final-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📸 截图展示

> **注**: 截图收集中，稍后补充。当前显示占位说明。

| Telegram 机器人界面 | 自动生成帖子 | 每日复盘报告 |
|---------------------|--------------|--------------|
| 🖼️ Bot 界面 | 🖼️ 发帖示例 | 🖼️ 复盘报告 |
| [查看占位说明](docs/screenshots/README.md) | [查看占位说明](docs/screenshots/README.md) | [查看占位说明](docs/screenshots/README.md) |

---

## ✨ 核心特性

- **多平台情报采集**: 聚合 X、Reddit、YouTube、TikTok、HackerNews 热点（基于 [last30days-skill](https://github.com/mvanhorn/last30days-skill)）
- **AI 内容生成**: 7 种预置语气（成人 UK、AI 工具、美妆、健身、加密、幽默、自定义）
- **OpenClaw 自动化**: 浏览器自动发帖/评论，3 层防封保护（随机延迟 + 内容变体 + 每日上限）
- **多 LLM 路由**: 支持 Claude、Groq、OpenAI 等
- **Telegram Bot 控制**: 简单命令（`/start`, `/set_niche`, `/trends`, `/review`）
- **每日复盘报告**: 自动化性能总结

---

## 🚀 3 分钟快速上手

1. **克隆仓库**:
   ```bash
   git clone https://github.com/sheldon010507-collab/x-agent.git
   cd x-agent/x-agent
   ```

2. **配置环境**:
   ```bash
   cp .env.example .env
   # 编辑 .env 填写密钥
   ```

3. **必填密钥**:
   - `TELEGRAM_BOT_TOKEN`: 从 [@BotFather](https://t.me/botfather) 获取
   - `TELEGRAM_CHAT_ID`: 你的 Telegram 聊天 ID
   - `SUPABASE_URL` & `SUPABASE_KEY`: [Supabase](https://supabase.com) 凭证
   - 至少一个 LLM API Key

4. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

5. **执行数据库迁移**:
   ```bash
   supabase db push
   ```

6. **启动 Agent**:
   ```bash
   python main.py
   ```

7. **Telegram 测试**: 发送 `/start` 给机器人

8. **（可选）安装 last30days CLI** 增强情报能力:
   ```bash
   pip install last30days
   ```

---

## 🎯 支持的 Niche 和语气

| Niche | 说明 | 命令 |
|-------|------|------|
| Adult UK | 英国成人用品 | `/set_niche adult_uk` |
| AI Tools | AI 工具评测 | `/set_niche ai_tools` |
| Beauty | 美妆产品评测 | `/set_niche beauty` |
| Fitness | 健身技巧激励 | `/set_niche fitness` |
| Crypto | 加密货币分析 | `/set_niche crypto` |
| Humor | 幽默内容 | `/set_niche humor` |
| Custom | 自定义语气 | `/set_niche custom` |

---

## 🏗️ 架构设计

```
x-agent/
├── main.py              # 入口
├── config.py            # 配置加载
├── modules/
│   ├── research.py      # 热点研究（last30days 集成）
│   ├── scorer.py        # 4 维评分（Relevance, Velocity, Authority, Convergence）
│   ├── generator.py     # AI 内容生成
│   ├── llm_router.py    # 多 LLM 路由
│   ├── openclaw_bridge.py # OpenClaw 自动化（含防封规则）
│   └── bot.py           # Telegram Bot 命令
├── prompts/             # A/B 测试 Prompt
├── niche_voices/        # Niche 专属语气模板
├── skills/              # OpenClaw Skills
├── migrations/          # Supabase 数据库迁移
├── data/                # 本地缓存和日志
└── tests/               # 单元测试
```

---

## 📚 文档

- **[3 分钟上手指南](docs/UP_AND_RUNNING.md)** - 完整启动清单
- **[部署指南](docs/DEPLOYMENT.md)** - 生产环境部署
- **[贡献指南](CONTRIBUTING.md)** - 如何贡献代码
- **[版本记录](docs/CHANGELOG.md)** - 更新历史

---

## 🛡️ 防封保护

X-Agent 实现 3 层防护：

1. **随机延迟**: 操作间隔 10-40 秒随机
2. **内容变体**: 随机 emoji 和句式变化
3. **每日上限**: 通过 `.env` 的 `MAX_COMMENTS_PER_DAY` 配置

---

## 🤝 贡献

欢迎贡献！我们需要的帮助：

- 新增 Niche 语气（`niche_voices/`）
- 优化 Prompt（`prompts/`）
- 新增平台支持（扩展 `research.py` 的 sources）
- 修复 Bug 或新增功能

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sheldon010507-collab/x-agent&type=Date)](https://star-history.com/#sheldon010507-collab/x-agent&Date)

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [last30days-skill](https://github.com/mvanhorn/last30days-skill) - 混合检索策略
- [OpenClaw](https://openclaw.ai) - 浏览器自动化框架
- 所有贡献者和支持者！

---

**用 ❤️ 构建 by sheldon010507-collab**

---

## English Version (Below)

# X-Agent v0

**X (Twitter) Intelligent Operations Agent**  
Hotspot Monitoring + AI Content Generation + OpenClaw Auto-Posting/Commenting + Daily Review

---

## ✨ Features

- **Multi-Platform Intelligence**: Aggregates trends from X, Reddit, YouTube, TikTok, HackerNews
- **AI Content Generation**: 7+ preset tones (Adult UK, AI Tools, Beauty, Fitness, Crypto, Humor, Custom)
- **OpenClaw Automation**: Browser-based posting/commenting with 3-layer anti-ban protection
- **Multi-LLM Routing**: Supports Claude, Groq, OpenAI, and more
- **Telegram Bot Control**: Simple commands (`/start`, `/set_niche`, `/trends`, `/review`)
- **Daily Review Reports**: Automated performance summaries

---

## 🚀 Quick Start (3 Minutes)

1. **Clone**:
   ```bash
   git clone https://github.com/sheldon010507-collab/x-agent.git
   cd x-agent/x-agent
   ```

2. **Configure**:
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   ```

3. **Required Keys**:
   - `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/botfather)
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
   - `SUPABASE_URL` & `SUPABASE_KEY`: [Supabase](https://supabase.com) credentials
   - At least one LLM API Key

4. **Install**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run Migrations**:
   ```bash
   supabase db push
   ```

6. **Start**:
   ```bash
   python main.py
   ```

7. **Test in Telegram**: Send `/start` to your bot

8. **(Optional) Install last30days CLI** for enhanced intelligence:
   ```bash
   pip install last30days
   ```

---

**Made with ❤️ by sheldon010507-collab**
