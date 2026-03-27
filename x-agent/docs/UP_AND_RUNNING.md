# UP_AND_RUNNING.md - 3分钟上手指南

## 快速开始

### 1. 克隆仓库并进入主目录

```bash
git clone https://github.com/yourusername/x-agent-v3.git
cd x-agent-v3/x-agent
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写 Telegram Bot Token、Supabase 等
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. （强烈推荐）安装 last30days CLI

```bash
pip install last30days
# 或按官方文档安装: https://github.com/mvanhorn/last30days-skill
```

> **注意**: last30days CLI 是可选增强模块，不安装也能正常运行（使用传统趋势源）。

### 5. 启动

```bash
python main.py
```

### 6. 在 Telegram 中测试

发送以下命令验证运行：

- `/start` — 今日热点概览
- `/set_niche ai_tools` — 切换 Niche
- `/trends` — 热点列表

---

## 前置要求

- Python 3.11+
- Telegram Bot Token (从 @BotFather 获取)
- Supabase 账号 (免费版即可)
- 至少一个 LLM API Key

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

### Q: last30days 未安装会怎样？

系统会自动使用 fallback 趋势源，不影响基本功能。安装后可获得更丰富的多平台数据。

### Q: 数据库连接失败？

确认 Supabase URL 和 Key 正确，检查是否在 Supabase 中执行了 `migrations/001_initial_schema.sql`。

---

## 下一步

- 阅读 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解生产部署
- 阅读 [CONTRIBUTING.md](../CONTRIBUTING.md) 参与开发
