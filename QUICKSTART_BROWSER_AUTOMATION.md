# X-Agent 浏览器自动化快速开始

你选择了**路线B（浏览器自动化）**。这是完全免费的方案，不需要付费 API，但有一定封号风险。

---

## 📋 需要的 API Keys 清单

### ✅ 必须配置（都可免费获取）

| Key | 获取方式 | 备注 |
|-----|---------|------|
| `TELEGRAM_BOT_TOKEN` | @BotFather (Telegram) | 免费，用于 Bot 驱动 |
| `SUPABASE_URL` | supabase.com | 免费层够用，数据库 |
| `SUPABASE_KEY` | 同上 | 同上 |
| **至少选一个 LLM Key** | 见下方 | 用于 AI 内容生成 |

### 🤖 LLM 供应商（选其中一个或多个）

| 供应商 | Key 名称 | 费用 | 推荐度 |
|--------|---------|------|--------|
| **Groq** | `GROQ_API_KEY` | ✅ **完全免费** | ⭐⭐⭐⭐⭐ 推荐测试 |
| Anthropic | `ANTHROPIC_API_KEY` | 按量付费 | ⭐⭐⭐⭐ 高质量 |
| OpenAI | `OPENAI_API_KEY` | 按量付费 | ⭐⭐⭐⭐ 推荐生产 |
| OpenRouter | `OPENROUTER_API_KEY` | 有免费模型 | ⭐⭐⭐ 备选 |

### 📊 研究功能（可选但推荐）

| Key | 获取方式 | 用途 |
|-----|---------|------|
| `REDDIT_CLIENT_ID` | reddit.com/prefs/apps | 免费，Reddit 热点研究 |
| `REDDIT_CLIENT_SECRET` | 同上 | 同上 |
| 无需 Key | - | Hacker News、Google Trends |

### ❌ X (Twitter) 不需要 API Key

浏览器自动化用**账号 Cookie**，而不是 API Key。只需账号和密码。

---

## 🚀 5 分钟快速开始

### 1️⃣ 克隆仓库

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent
```

### 2️⃣ 创建环境配置文件

```bash
cp .env.example .env
```

### 3️⃣ 编辑 `.env` 并填入 Keys

**最小配置（测试用）**：

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl...  # @BotFather 获取
TELEGRAM_CHAT_ID=-1001234567890                # 你的 Telegram 频道/群组 ID

# Supabase（数据库）
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# LLM（选 Groq 免费）
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx         # https://groq.com

# 防封配置（可选）
DELAY_MIN=10
DELAY_MAX=40
MAX_POSTS_PER_DAY=10
MAX_COMMENTS_PER_DAY=15
```

**完整配置（推荐）**：

```bash
# === Telegram ===
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx

# === Database ===
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# === LLM（推荐用 Groq）===
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# === Reddit 热点研究 ===
REDDIT_CLIENT_ID=xxxxxxxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxx

# === 防封配置 ===
DELAY_MIN=10
DELAY_MAX=40
MAX_POSTS_PER_DAY=10
MAX_COMMENTS_PER_DAY=15
```

### 4️⃣ 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 5️⃣ 初始化 X 登录

**方式 A：Python CLI（推荐）**

```bash
python -c "
import asyncio
from modules.x_automation import create_x_automation

async def login():
    auto = await create_x_automation()
    email = input('X 邮箱/用户名: ')
    pwd = input('密码: ')
    ok = await auto.login(email, pwd)
    if ok: print('✅ 登录成功！')
    else: print('❌ 登录失败')
    await auto.close()

asyncio.run(login())
"
```

**方式 B：启动 Bot 后通过 Telegram**

```bash
python main.py
```

在 Telegram 中：

```
/xconfigure
```

### 6️⃣ 启动 Bot

```bash
python main.py
```

会看到：

```
✅ Bot initialized
🚀 Starting Bot polling...
```

### 7️⃣ 在 Telegram 中测试

```
/start                    # 显示欢迎信息
/create a                 # 生成 A 类推文
✅ 人工确认发布            # 点击按钮
✓ 确认无误，发布          # 再点一次（二次确认）
```

然后查看 X 账号，推文应该已发布！

---

## 📍 Key 获取指南

### Telegram Bot Token

1. 打开 Telegram，搜索 **@BotFather**
2. 发送 `/newbot`
3. 按提示取名字（例如 `x_agent_bot`）
4. 得到 Token，复制到 `.env` 中的 `TELEGRAM_BOT_TOKEN`
5. 发送 `/mybots` 找到你的 Bot，点击设置
6. 获取 Chat ID（或在群组中 `/start`，查看日志）

### Supabase

1. 访问 https://supabase.com
2. 注册（用 GitHub 最快）
3. 创建新 Project（选择离你最近的区域）
4. 等待项目启动（1-2 分钟）
5. 侧边栏 → Settings → API Keys
6. 复制 `Project URL` 和 `anon public` key

### Groq API Key（完全免费）

1. 访问 https://groq.com
2. 点击 "Get API Key"
3. 注册账号
4. 创建新 API Key
5. 复制到 `.env` 中的 `GROQ_API_KEY`

**特点**：
- ✅ 完全免费
- ✅ Llama 3.3 70B（非常强大）
- ✅ 速度快（Token 生成很快）
- ✅ 无付费限制（目前）

### Reddit Client ID/Secret

1. 访问 https://reddit.com/prefs/apps
2. 登录你的 Reddit 账号
3. 滚到页面底部，点 "Create another app"
4. 名字：`x-agent`，类型：`script`
5. 填入 Redirect URI：`http://localhost:8080`
6. 点 Create
7. 复制 ID（在名字下）和 Secret

---

## 🔐 安全提示（很重要！）

### 1. 账号封号风险

- ⚠️ **X (Twitter) 2026 年风控很强**
- 建议用**小号测试**，不要用主账号
- 设置合理的每日限额（不要一次发 100 条）
- 遵守间隔延迟（10-40 秒）

### 2. 凭证安全

```bash
# ✅ DO：保护你的 .env
chmod 600 .env
echo ".env" >> .gitignore

# ❌ DON'T：上传到 GitHub
git add .env          # ❌ 不要
git add .env.example  # ✅ 只提交示例

# ❌ DON'T：在公共电脑上运行
# Session 保存在 ~/.x-agent/sessions/
# 其他人可能窃取你的账号
```

### 3. Session 文件保护

登录后，session 保存在：

```
~/.x-agent/sessions/x_auth_state.json
```

这包含你的登录状态（Cookie）。**不要分享此文件**。

---

## 📊 工作流程

```
你在 Telegram 中：

/create a
  ↓
Bot 生成 AI 推文（A 类，3 条备选）
  ↓
你看到内容和风险评分
  ↓
点击 [✅ 人工确认发布] 按钮
  ↓
二次确认对话框弹出
  ↓
点击 [✓ 确认无误，发布]
  ↓
Playwright 无头浏览器自动：
  1. 打开 X.com
  2. 登录（用保存的 session）
  3. 点击发帖
  4. 输入内容
  5. 点击发布
  ↓
✅ 推文已发布到 X!

你可以在 X 上看到新推文
```

---

## 🛡️ 防封机制

系统自动为你做以下防护：

### 1. 随机延迟

每条操作前延迟 **10-40 秒**（可配置）

```python
delay = random.uniform(10, 40)  # 防止被检测为 bot
```

### 2. 内容变体

自动添加不同 emoji 和短语

```
原文：  "新工具发布了！"
变体1： "新工具发布了！ 🔥"
变体2： "新工具发布了！ Interesting."
变体3： "新工具发布了！ 💡 What do you think?"
```

### 3. 每日上限

```
MAX_POSTS_PER_DAY=10       # 最多每天 10 条
MAX_COMMENTS_PER_DAY=15    # 最多每天 15 条评论
MAX_LIKES_PER_DAY=30       # 最多每天 30 个赞
```

### 4. 二次人工确认

**所有发帖都需要你手动确认两次**，防止误操作

```
✅ 人工确认 → ⚠️ 再次确认 → 发布
```

---

## 📝 常见问题

**Q: 为什么要手动登录一次？**

A: 浏览器自动化需要登录状态（Cookie）。手动登录一次后，自动化会复用这个 session，无需每次重新输入密码。

**Q: 密码是否安全？**

A: 登录后，密码不会被保存。只有 Cookie（session）被保存到本地。如果担心，用一次性密码。

**Q: 可以同时在多个设备上运行吗？**

A: 不推荐。X 会检测同一账号的多处登录，可能导致验证要求。建议在一个设备上运行。

**Q: 发帖失败怎么办？**

A: 检查日志：

```bash
grep ERROR ~/.x-agent/x_agent.log
```

常见原因：
- Session 过期 → 重新登录
- 网络问题 → 检查连接
- 账号被限制 → 检查 X 应用设置

**Q: 如何只启用评论，不发帖？**

A: 在 `.env` 中：

```bash
AUTO_POST_ENABLED=false
AUTO_COMMENT_ENABLED=true
AUTO_LIKE_ENABLED=false
```

**Q: 可以自定义 Niche 吗？**

A: 可以。在 Telegram 中：

```
/set_niche
```

选择 7 种预设 Niche 或自定义。Bot 会自动调整语气。

---

## 🎯 完整检查清单

- [ ] Fork/Clone 仓库
- [ ] 创建 `.env` 文件
- [ ] 获取 `TELEGRAM_BOT_TOKEN`（@BotFather）
- [ ] 获取 `SUPABASE_URL` + `SUPABASE_KEY`
- [ ] 获取 `GROQ_API_KEY`（或其他 LLM）
- [ ] 获取 `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET`（可选）
- [ ] `pip install -r requirements.txt`
- [ ] `playwright install chromium`
- [ ] 初始化 X 登录（`python login_x.py` 或 `/xconfigure`）
- [ ] `python main.py` 启动 Bot
- [ ] Telegram 中 `/create a` 测试

---

## 📞 需要帮助？

- 查看详细文档：`docs/BROWSER_AUTOMATION_SETUP.md`
- 查看日志：`~/.x-agent/x_agent.log`
- 检查 session：`~/.x-agent/sessions/x_auth_state.json` 是否存在
- 查看源代码：`modules/x_automation.py`

---

## ✅ 下一步

1. 现在就创建 `.env` 文件
2. 填入必要的 API Keys
3. 运行 `python main.py`
4. 在 Telegram 中发送 `/create a`
5. 看你的第一条 AI 生成的推文自动发布到 X！

**祝你使用愉快！🚀**
