# X-Agent v3.0 - 5分钟上手指南

## 前置要求

- Python 3.9+
- Telegram Bot Token (从 @BotFather 获取)
- Supabase 账号 (免费版即可)
- 至少一个 LLM API Key

## 快速开始 Checklist

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/x-agent.git
cd x-agent
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下必要信息：

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here

# LLM API Keys (至少填一个)
OPENAI_API_KEY=sk-...
# 或者
ANTHROPIC_API_KEY=sk-ant-...
# 或者
GEMINI_API_KEY=...
```

### 3. 初始化数据库

```bash
# 使用 Supabase CLI
supabase db push

# 或者手动执行 SQL
# 复制 migrations/001_initial_schema.sql 内容到 Supabase SQL Editor 执行
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 启动服务

```bash
# 直接运行
python main.py

# 或者使用 PM2 (推荐生产环境)
pm2 start main.py --name x-agent
```

### 6. 验证运行

在 Telegram 中发送：

1. `/start` - 应该显示热点概览
2. `/set_niche adult_uk` - 切换到成人用品模式
3. `/trends` - 查看当前热点

看到正确响应即表示成功！

## 支持的 Niche 模式

| 命令 | 领域 |
|-----|-----|
| `/set_niche adult_uk` | 成人用品 (英国市场) |
| `/set_niche ai_tools` | AI 工具评测 |
| `/set_niche beauty` | 美妆护肤 |
| `/set_niche fitness` | 健身健康 |
| `/set_niche crypto` | 加密货币 |
| `/set_niche humor` | 幽默段子 |
| `/set_niche custom` | 自定义模式 |

## 常见问题

### Q: 启动后没有反应？

检查 Telegram Bot Token 是否正确，可以用浏览器访问：
```
https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Q: 数据库连接失败？

确认 Supabase URL 和 Key 正确，检查是否在 Supabase 中创建了必要的表。

### Q: 内容生成失败？

确认至少配置了一个有效的 LLM API Key，查看日志文件 `data/x-agent.log`。

## 下一步

- 阅读 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解生产部署
- 阅读 [CONTRIBUTING.md](../CONTRIBUTING.md) 参与开发
- 加入社区讨论
