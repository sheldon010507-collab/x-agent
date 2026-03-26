# UP_AND_RUNNING.md — 5分钟上手指南

## 前置条件

- Python 3.10+
- Supabase 账号
- Telegram Bot Token
- 至少一个 LLM API Key

## 快速启动 Checklist

- [ ] 1. Clone 仓库，进入 `x-agent/` 目录
- [ ] 2. `cp .env.example .env`，填入至少一个 LLM API Key
- [ ] 3. 填入 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`
- [ ] 4. 填入 `SUPABASE_URL` 和 `SUPABASE_KEY`
- [ ] 5. 运行 `supabase db push` 完成建表
- [ ] 6. `pip install -r requirements.txt`
- [ ] 7. `python main.py` 启动（或 `pm2 start main.py`）
- [ ] 8. Telegram 发送 `/start`，看到热点概览即成功
- [ ] 9. 发送 `/set_niche adult_uk` 切换至成人用品模式
- [ ] 10. 发送 `/trends` 查看第一批热点

---

## 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | ✅ | BotFather 创建的 Token |
| `TELEGRAM_CHAT_ID` | ✅ | 接收消息的 Chat ID |
| `SUPABASE_URL` | ✅ | Supabase 项目 URL |
| `SUPABASE_KEY` | ✅ | Supabase anon key |
| `OPENAI_API_KEY` | ⚪ | OpenAI API Key（任选一个） |
| `ANTHROPIC_API_KEY` | ⚪ | Claude API Key |
| `GEMINI_API_KEY` | ⚪ | Gemini API Key |
| `GROQ_API_KEY` | ⚪ | Groq API Key |
| `DEEPSEEK_API_KEY` | ⚪ | DeepSeek API Key |

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `/start` | 启动 Bot，显示热点概览 |
| `/trends` | 查看当前热点 |
| `/set_niche <name>` | 切换 Niche 模式 |
| `/generate_a` | 生成 A 类推文 |
| `/generate_b` | 生成 B 类视频脚本 |
| `/generate_c` | 生成智能评论 |
| `/settings` | 打开设置面板 |
| `/help` | 显示帮助 |

---

## 预置 Niche

- `adult_uk` — 成人用品（英国市场）
- `ai_tools` — AI 工具推荐
- `beauty` — 美妆护肤
- `fitness` — 健身运动
- `crypto` — 加密货币
- `humor` — 幽默段子
- `custom` — 自定义

---

## 目录结构

```
x-agent/
├── main.py           # 主入口
├── bot.py            # Telegram Bot
├── config.py         # 配置管理
├── modules/          # 核心模块
│   ├── database.py
│   ├── llm_router.py
│   ├── research.py
│   ├── scorer.py
│   ├── generator.py
│   ├── openclaw_bridge.py
│   └── scheduler.py
├── prompts/          # Prompt 模板
├── niche_voices/     # 语气文件
├── migrations/       # 数据库 Schema
└── tests/            # 单元测试
```

---

## 常见问题

### Q: LLM API 调用失败？

检查 API Key 是否正确，网络是否通畅。系统会自动 fallback 到其他供应商。

### Q: Supabase 连接失败？

确认 `SUPABASE_URL` 和 `SUPABASE_KEY` 正确，检查 Supabase 项目状态。

### Q: Telegram Bot 无响应？

确认 Bot Token 正确，Chat ID 正确（群组需要负数 ID）。

---

## 下一步

- 阅读 [CONFIG.md](../x-agent/CONFIG.md) 了解详细配置
- 阅读 [DEPLOYMENT.md](../x-agent/DEPLOYMENT.md) 了解生产部署
- 查看 [CODE_REVIEW.md](../x-agent/CODE_REVIEW.md) 了解代码架构
