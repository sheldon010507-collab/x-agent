# DEPLOYMENT.md - 部署指南

## 快速部署

### 1. 环境要求

- Python 3.11+
- Docker (可选)
- Telegram Bot Token
- Supabase 账号

### 2. 本地部署

```bash
# 克隆仓库
git clone https://github.com/your-repo/x-agent-v3.git
cd x-agent-v3

# 进入主目录
cd x-agent

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填写必要配置
nano .env
```

### 3. 必填配置

在 `.env` 中填写：

```bash
# Telegram Bot Token (必填)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl

# Telegram Chat ID (必填)
TELEGRAM_CHAT_ID=-1001234567890

# Supabase (必填)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGci...

# LLM Provider (至少配置一个)
ANTHROPIC_API_KEY=sk-ant-xxx
# 或
GROQ_API_KEY=gsk_xxx
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 启动

```bash
python main.py
```

---

## last30days CLI 安装（可选增强模块）

last30days 是一个多平台深度研究工具，可以显著提升情报能力。

### 安装方式

```bash
# 方式 1: pip 安装
pip install last30days

# 方式 2: 从源码安装
git clone https://github.com/mvanhorn/last30days-skill.git
cd last30days-skill
pip install -e .
```

### 验证安装

```bash
last30days "AI tools" --days=7 --sources=x,reddit,youtube --agent --output=json
```

### 注意事项

- **last30days 是可选模块**：不安装也能正常运行，会使用 fallback 趋势源
- 安装后可以获取更丰富的多平台数据（X + Reddit + YouTube + TikTok + Hacker News 等）
- 详见: https://github.com/mvanhorn/last30days-skill

---

## Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f x-agent
```

### Docker Compose 配置

```yaml
services:
  x-agent:
    build: ./x-agent
    volumes:
      - ./x-agent/data:/app/data
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped
```

---

## Supabase 数据库初始化

1. 登录 [Supabase Dashboard](https://supabase.com)
2. 创建新项目
3. 在 SQL Editor 中运行 `migrations/001_initial_schema.sql`

### 数据表结构

- `trends` — 热点记录
- `content_queue` — 内容草稿
- `daily_log` — 每日数据录入
- `strategy` — 策略版本
- `automation_settings` — 自动化配置

---

## 常见问题

### Q: last30days 未安装会怎样？

A: 系统会自动使用 fallback 趋势源，不影响基本功能。

### Q: Telegram Bot Token 如何获取？

A: 在 Telegram 搜索 @BotFather，发送 `/newbot` 创建 Bot。

### Q: Chat ID 如何获取？

A: 向 @userinfobot 发送任意消息获取你的 Chat ID。

---

## 生产环境建议

1. 使用 PM2 管理进程（推荐）
   ```bash
   npm install -g pm2
   pm2 start main.py --name x-agent --interpreter python3
   pm2 save && pm2 startup
   ```

2. 配置日志轮转

3. 设置监控告警

4. 定期备份数据库

---

## 版本信息

- **当前版本**: v0 Final (2026-03-27)
- **更新日志**: 见 `docs/CHANGELOG.md`
