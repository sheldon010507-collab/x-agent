# UP_AND_RUNNING.md - 3 分钟上手指南

## 快速启动清单

完成以下步骤，3 分钟内让 X-Agent 跑起来：

- [ ] **1. 克隆仓库并进入主目录**
  ```bash
  git clone https://github.com/sheldon010507-collab/x-agent.git
  cd x-agent/x-agent
  ```

- [ ] **2. 复制环境配置文件**
  ```bash
  cp .env.example .env
  ```

- [ ] **3. 填写必要密钥** (编辑 `.env`)
  - `TELEGRAM_BOT_TOKEN` - 从 [@BotFather](https://t.me/botfather) 获取
  - `TELEGRAM_CHAT_ID` - 你的 Telegram 聊天 ID
  - `SUPABASE_URL` - Supabase 项目 URL
  - `SUPABASE_KEY` - Supabase API Key
  - 至少一个 LLM API Key (Claude/Groq/OpenAI 等)

- [ ] **4. 安装依赖**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **5. 执行数据库迁移**
  ```bash
  supabase db push
  ```

- [ ] **6. 启动 Agent**
  ```bash
  python main.py
  ```

- [ ] **7. Telegram 测试**
  - 发送 `/start` 给机器人
  - 看到欢迎信息即成功

- [ ] **8. (可选) 安装 last30days CLI**
  ```bash
  pip install last30days
  ```
  > **说明**: last30days 是可选增强模块，不安装也能正常运行（使用传统趋势源）。安装后情报能力更强，支持多平台 30 天真实数据。

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `/start` | 查看欢迎信息和帮助 |
| `/set_niche <niche>` | 切换 Niche 语气（如 `adult_uk`, `ai_tools`） |
| `/trends` | 查看当前热点趋势 |
| `/review` | 生成每日复盘报告 |
| `/status` | 查看运行状态 |

---

## 预置 Niche 列表

- `adult_uk` - 英国成人用品
- `ai_tools` - AI 工具
- `beauty` - 美妆
- `fitness` - 健身
- `crypto` - 加密货币
- `humor` - 幽默
- `custom` - 自定义

---

## 遇到问题？

1. 检查 `.env` 文件是否填写完整
2. 确认 Python 版本 >= 3.9
3. 查看日志文件 `data/x-agent.log`
4. 在 GitHub 提 Issue 或加入讨论组

---

## 下一步

- 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解生产环境部署
- 查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 参与贡献
- 访问 [CHANGELOG.md](CHANGELOG.md) 了解版本更新记录

**祝使用愉快！** 🚀
