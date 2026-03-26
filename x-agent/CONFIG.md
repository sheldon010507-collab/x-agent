# X-Agent v3.0 配置指南

本指南详细说明所有配置项的获取方式和填写说明。

---

## 📋 .env.example 字段说明

### 必填配置

#### Telegram 配置

```bash
# Telegram Bot Token (必填)
# 获取方式：在 Telegram 中搜索 @BotFather，发送 /newbot 创建 Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-6789jklmnopqrst

# Telegram 聊天 ID (必填)
# 获取方式：向 @userinfobot 发送任意消息，或从 Bot 日志中查看
TELEGRAM_CHAT_ID=-1001234567890
```

**如何获取 Telegram Bot Token：**

1. 打开 Telegram，搜索 `@BotFather`
2. 发送 `/newbot` 创建新 Bot
3. 按提示设置 Bot 名称（如 `My X Agent`）
4. 设置 Bot 用户名（必须以 `bot` 结尾，如 `my_x_agent_bot`）
5. BotFather 会返回 Token，格式如：
   ```
   123456:ABC-DEF1234ghIkl-6789jklmnopqrst
   ```
6. 将 Token 复制到 `.env` 文件的 `TELEGRAM_BOT_TOKEN`

**如何获取 Telegram Chat ID：**

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息，Bot 会返回你的 Chat ID
3. 或先将 Bot 添加到群组，然后在群组发送消息，从日志中查看 Chat ID
4. 群组 Chat ID 通常为负数，如 `-1001234567890`

---

#### Supabase 配置

```bash
# Supabase 项目 URL (必填)
# 获取方式：在 Supabase 控制台 -> Settings -> API
SUPABASE_URL=https://abcdefghijklmnopqrst.supabase.co

# Supabase API Key (必填)
# 获取方式：在 Supabase 控制台 -> Settings -> API -> project api keys
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**如何获取 Supabase 配置：**

1. 访问 [supabase.com](https://supabase.com) 注册账号
2. 点击 "New Project" 创建项目
   - 选择组织（或创建新组织）
   - 设置项目名称
   - 设置数据库密码（记住此密码）
   - 选择区域（建议选离你近的）
3. 项目创建完成后，进入控制台
4. 点击左侧 "Settings" (齿轮图标) -> "API"
5. 复制以下内容：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **project api keys** 下的 `anon` 或 `service_role` key
6. 初始化数据库：
   - 在 Supabase 控制台左侧点击 "SQL Editor"
   - 点击 "New query"
   - 复制 `migrations/001_initial_schema.sql` 的全部内容
   - 粘贴到 SQL 编辑器并运行（Run）
   - 确认创建 6 张表：`trends`, `content_queue`, `daily_log`, `strategy`, `automation_settings`, `llm_config`

---

#### LLM 供应商配置

至少需要配置一个 LLM 供应商的 API Key。

```bash
# Anthropic API Key (推荐)
# 获取方式：https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key
# 获取方式：https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Groq API Key (免费额度高)
# 获取方式：https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# Gemini API Key
# 获取方式：https://makersuite.google.com/app/apikey
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# OpenRouter API Key (聚合多个模型)
# 获取方式：https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx

# NVIDIA NIM API Key
# 获取方式：https://build.nvidia.com/explore/discover
NVIDIA_NIM_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# Ollama 本地部署 (无需 API Key)
OLLAMA_BASE_URL=http://localhost:11434
```

**各 LLM 供应商 API Key 获取方式：**

**1. Anthropic (推荐)**
- 访问：https://console.anthropic.com
- 注册/登录账号
- 点击 "API Keys" -> "Create Key"
- 复制 Key 到 `.env`

**2. OpenAI**
- 访问：https://platform.openai.com
- 注册/登录账号
- 点击右上角头像 -> "View API keys"
- 点击 "Create new secret key"
- 复制 Key 到 `.env`

**3. Groq (免费额度高)**
- 访问：https://console.groq.com
- 使用 GitHub 账号登录
- 点击 "API Keys" -> "Create API Key"
- 复制 Key 到 `.env`

**4. Gemini**
- 访问：https://makersuite.google.com/app/apikey
- 使用 Google 账号登录
- 点击 "Create API key"
- 复制 Key 到 `.env`

**5. OpenRouter (聚合模型)**
- 访问：https://openrouter.ai
- 注册/登录账号
- 点击 "Keys" -> "Create Key"
- 复制 Key 到 `.env`

**6. NVIDIA NIM**
- 访问：https://build.nvidia.com
- 注册/登录账号
- 点击 "API Keys" -> "Generate Key"
- 复制 Key 到 `.env`

**7. Ollama (本地部署)**
- 访问：https://ollama.com
- 下载安装 Ollama
- 终端运行：`ollama pull llama3.2`
- 无需 API Key，保持 `OLLAMA_BASE_URL=http://localhost:11434`

---

### 选填配置

```bash
# 默认 LLM 供应商 (选填，默认：anthropic)
LLM_PROVIDER=anthropic

# 默认模型 (选填，默认：claude-3-5-sonnet-20241022)
LLM_MODEL=claude-3-5-sonnet-20241022

# OpenRouter 基础 URL (选填，默认已设置)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# NVIDIA NIM 基础 URL (选填，默认已设置)
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1

# Reddit API 配置 (选填，用于 PRAW 数据源)
REDDIT_CLIENT_ID=xxxxxxxxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxx
REDDIT_USER_AGENT=x-agent/3.0

# OpenClaw API 端点 (选填，默认：http://localhost:8080)
OPENCLAW_API_ENDPOINT=http://localhost:8080

# 加密密钥 (选填，首次启动自动生成)
ENCRYPTION_KEY=
```

---

## 🔧 OpenClaw 安装和配置指南

### OpenClaw 是什么？

OpenClaw 是一个 X (Twitter) 自动化工具，用于将生成的内容自动发布到 X 平台。

### 安装步骤

**1. 安装 Node.js (v18+)**

```bash
# macOS
brew install node

# Linux
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# 访问 https://nodejs.org 下载安装包
```

**2. 安装 OpenClaw**

```bash
npm install -g openclaw
```

**3. 配置 OpenClaw**

```bash
# 初始化配置
openclaw init

# 登录 X 账号
openclaw login

# 启动 Gateway 服务
openclaw gateway start
```

**4. 验证连接**

```bash
# 检查 OpenClaw 状态
openclaw gateway status
```

**5. 在 .env 中配置 OpenClaw**

```bash
OPENCLAW_API_ENDPOINT=http://localhost:8080
```

### 不使用 OpenClaw 可以吗？

可以！如果只需要生成内容而不自动发布，可以不配置 OpenClaw。应用会正常启动，只是不会执行自动发布功能。

---

## 🔍 配置验证

启动应用前，可以使用配置验证工具检查配置是否正确：

```bash
python3 -c "
import asyncio
from modules.config_validator import ConfigValidator

async def check():
    validator = ConfigValidator()
    report = await validator.validate_all()
    print(report['summary'])
    
asyncio.run(check())
```

验证项目包括：
- ✅ 环境变量必填项检查
- ✅ OpenClaw 连接检查
- ✅ Supabase 连接检查
- ✅ LLM API Key 有效性检查

---

## 🛡️ 安全建议

1. **不要将 `.env` 文件提交到 Git**
   - 项目已包含 `.gitignore`，自动忽略 `.env`
   - 不要将 `.env` 截图或分享给他人

2. **使用服务角色 Key**
   - Supabase 提供 `anon` 和 `service_role` 两种 Key
   - 建议使用 `service_role` key（权限更高）
   - 不要将 Key 泄露给他人

3. **定期更换 API Key**
   - 定期在相应平台重新生成 API Key
   - 发现异常活动时立即更换

4. **使用环境变量**
   - 生产环境建议使用系统环境变量
   - 不要将敏感信息硬编码到代码中

---

## 📝 配置示例（脱敏）

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-6789jklmnopqrst
TELEGRAM_CHAT_ID=-1001234567890

# Supabase
SUPABASE_URL=https://abcdefghijklmnopqrst.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...

# LLM (至少配置一个)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
# GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxx
# OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
# NVIDIA_NIM_API_KEY=xxxxxxxxxxxxxxxxxxxxx

# 默认 LLM 配置
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022

# OpenClaw
OPENCLAW_API_ENDPOINT=http://localhost:8080

# 加密密钥（自动生成，勿手动修改）
ENCRYPTION_KEY=
```

---

## ❓ 常见问题

### Q: 配置后启动仍报错？

**A**: 运行配置验证工具检查具体哪一项未通过：
```bash
python3 modules/config_validator.py
```

### Q: 可以只使用免费额度吗？

**A**: 可以！推荐组合：
- Groq: 免费额度高，速度快
- Ollama: 本地部署，完全免费
- Gemini: 免费额度足够日常使用

### Q: 多个 LLM 供应商如何切换？

**A**: 在 Bot 中使用 `/llm` 命令，通过 Inline 按钮动态切换。

### Q: 配置修改后需要重启吗？

**A**: 是的，修改 `.env` 后需要重启应用才能生效。

---

**最后更新**: 2026-03-25  
**版本**: v3.0.0
