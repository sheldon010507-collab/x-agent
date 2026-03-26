# X-Agent v3.0 — 5分钟上手指南

## 准备工作

确保你有以下账号：
- [ ] Telegram Bot Token（从 @BotFather 获取）
- [ ] Supabase 项目（免费版即可）
- [ ] 至少一个 LLM API Key（Claude/OpenAI/Groq/Gemini 任选）

---

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
| `DEEPSEEK_API_KEY` | ⚪ | DeepSeek API Key |

---

## 常用命令

```bash
# 启动
python main.py

# 后台运行
pm2 start main.py --name x-agent

# 查看日志
pm2 logs x-agent

# 停止
pm2 stop x-agent
```

---

## 支持的 Niche

- `adult_uk` - 英国成人用品（默认）
- `ai_tools` - AI 工具
- `beauty` - 美妆
- `fitness` - 健身
- `crypto` - 加密货币
- `humor` - 幽默段子
- `custom` - 自定义

使用 `/set_niche <name>` 切换。

---

## 故障排查

### Bot 不响应
1. 检查 `TELEGRAM_BOT_TOKEN` 是否正确
2. 检查 Bot 是否被踢出群组
3. 检查 `TELEGRAM_CHAT_ID` 是否匹配

### last30days 命令未找到
```bash
clawhub install last30days
```

### OpenClaw 未启动
```bash
openclaw gateway start
```

### 数据库连接失败
1. 检查 Supabase 项目是否正常运行
2. 检查 `SUPABASE_URL` 和 `SUPABASE_KEY`
3. 检查是否运行过 `supabase db push`

### 无热点生成
1. 检查 LLM API Key 是否有效
2. 检查网络连接
3. 查看 `data/x-agent.log` 日志

---

## 下一步

- 阅读 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解生产部署
- 阅读 [CONFIG.md](./CONFIG.md) 了解高级配置
- 尝试不同 Niche
- 调整自动化设置
- 查看每日复盘

祝使用愉快！ 🚀
