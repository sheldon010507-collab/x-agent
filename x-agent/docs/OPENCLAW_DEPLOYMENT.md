# X-Agent OpenClaw 部署完全指南

> **OpenClaw** 是一个强大的 X（Twitter）自动化平台，提供发帖、评论、点赞等自动化功能。
> 本指南将带你完整部署 X-Agent 与 OpenClaw 的集成。

---

## 📋 部署架构

```
┌─────────────────────────────────────┐
│         X-Agent (你的Bot)           │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │   Research Module           │   │
│  │ (多平台热点采集)            │   │
│  └────────────────┬────────────┘   │
│                   │                 │
│  ┌────────────────▼────────────┐   │
│  │   Scorer Module             │   │
│  │ (评分 + 风险评估)            │   │
│  └────────────────┬────────────┘   │
│                   │                 │
│  ┌────────────────▼────────────┐   │
│  │   Content Generator         │   │
│  │ (生成A/B/C类内容)           │   │
│  └────────────────┬────────────┘   │
│                   │                 │
│  ┌────────────────▼────────────┐   │
│  │   Telegram Bot              │   │
│  │ (人工审核 + 二步确认)       │   │
│  └────────────────┬────────────┘   │
│                   │                 │
│  ┌────────────────▼────────────┐   │
│  │   OpenClaw Bridge           │   │
│  │ (防封机制)                  │   │
│  └────────────────┬────────────┘   │
└─────────────────┼─────────────────┘
                  │
            [OpenClaw API]
                  │
    ┌─────────────┴──────────────┐
    ▼                            ▼
[OpenClaw Server]          [X (Twitter)]
  - 发帖                     - 用户时间线
  - 评论                     - 互动数据
  - 点赞                     - 账户信息
  - 转发
```

---

## 🚀 完整部署步骤

### Step 1: 获取 OpenClaw 账户

#### A. 注册 OpenClaw
```bash
# 访问 OpenClaw 官方网站
https://openclaw.io  # 或替换为实际URL

# 或使用 CLI 快速设置
openclaw auth login
```

#### B. 获取 API 密钥
```bash
# 登录后在 Dashboard 获取
Settings → API Keys → Generate New Key

保存以下信息：
- API_KEY: openclaw_xxx...
- API_SECRET: secret_xxx...
- ENDPOINT: https://api.openclaw.io/v1  (或本地)
```

#### C. 关联 X（Twitter）账户
```bash
# 在 OpenClaw Dashboard
Connected Accounts → Link Twitter
→ 使用浏览器授权（OAuth）
→ 确认接受权限
```

---

### Step 2: 配置 X-Agent

#### 更新 `.env` 文件

```bash
# 在 x-agent 项目根目录
nano .env
```

**添加以下配置**:

```env
# ========== OpenClaw 配置 ==========
OPENCLAW_ENABLED=true
OPENCLAW_API_KEY=your_api_key_here
OPENCLAW_API_SECRET=your_api_secret_here
OPENCLAW_API_ENDPOINT=http://localhost:8080  # 本地开发
# OPENCLAW_API_ENDPOINT=https://api.openclaw.io/v1  # 生产环境

# ========== 防封机制 ==========
DELAY_MIN=10          # 最小延迟秒数
DELAY_MAX=40          # 最大延迟秒数
MAX_POSTS_PER_DAY=5   # 每日最多发帖数
MAX_COMMENTS_PER_DAY=15  # 每日最多评论数
MAX_LIKES_PER_DAY=30  # 每日最多点赞数

# ========== 其他配置 ==========
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ANTHROPIC_API_KEY=your_anthropic_key
```

---

### Step 3: 集成到 Bot

#### 修改 `bot_v0_final.py`

在处理用户确认发布时，调用 OpenClaw：

```python
# modules/bot_v0_final.py - 修改 button_callback 方法

async def button_callback(self, update: Update, context: CallbackContext) -> None:
    # ... 现有代码 ...

    if action == "final":
        if sub_action == "confirm_publish":
            # 第二步确认通过，调用OpenClaw发布

            # 1. 获取用户生成的内容
            user_id = query.from_user.id
            generated = self.user_states.get(user_id, {}).get("generated", {})

            # 2. 初始化OpenClaw桥接
            openclaw = create_openclaw_bridge()

            # 3. 调用发帖API
            result = await openclaw.post_content(
                content=generated.get("content"),
                niche=self.config.get("niche", "general"),
                apply_variant=True  # 自动应用内容变体
            )

            # 4. 反馈用户
            if result["success"]:
                await query.edit_message_text(
                    f"✅ **发帖成功！**\n\n"
                    f"Post ID: {result.get('post_id')}\n"
                    f"URL: {result.get('url')}\n\n"
                    f"已通过 OpenClaw 发布到 X",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"❌ **发帖失败**\n\n"
                    f"原因: {result.get('reason')}\n\n"
                    f"请检查 OpenClaw 配置",
                    parse_mode="Markdown"
                )
```

#### 在 `main.py` 中初始化 OpenClaw

```python
# main.py

from modules.openclaw_bridge import create_openclaw_bridge

class XAgentApp:
    async def initialize(self):
        # ... 现有代码 ...

        # 初始化 OpenClaw
        self.openclaw = create_openclaw_bridge(
            api_endpoint=os.getenv(
                "OPENCLAW_API_ENDPOINT",
                "http://localhost:8080"
            )
        )

        # 检查连接
        health = await self.openclaw.check_health()
        if health["status"] == "ok":
            logger.info("✅ OpenClaw 已连接")
        else:
            logger.warning("⚠️ OpenClaw 未可用，将使用模拟模式")
```

---

### Step 4: 本地 OpenClaw 服务器设置

#### 选项 A: Docker 容器运行

```bash
# 1. 拉取 OpenClaw 镜像
docker pull openclaw/openclaw:latest

# 2. 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    ports:
      - "8080:8080"
    environment:
      - OPENCLAW_PORT=8080
      - LOG_LEVEL=info
    volumes:
      - openclaw_data:/app/data
    restart: unless-stopped

volumes:
  openclaw_data:
EOF

# 3. 启动服务
docker-compose up -d

# 4. 验证
curl http://localhost:8080/health
# 应返回: {"status":"ok"}
```

#### 选项 B: 本地安装

```bash
# 1. 安装 OpenClaw CLI
pip install openclaw-cli

# 2. 启动本地服务器
openclaw server start --port 8080

# 3. 验证
openclaw health check
```

---

### Step 5: 测试集成

#### A. 单元测试

```bash
# 运行 OpenClaw 相关测试
pytest x-agent/tests/test_openclaw_integration.py -v
```

#### B. 手动测试

```python
# test_openclaw_manual.py

import asyncio
from modules.openclaw_bridge import create_openclaw_bridge

async def test_openclaw():
    # 1. 初始化
    openclaw = create_openclaw_bridge(
        api_endpoint="http://localhost:8080"
    )

    # 2. 测试健康检查
    health = await openclaw.check_health()
    assert health["status"] == "ok"
    print("✅ OpenClaw 连接成功")

    # 3. 测试发帖（模拟）
    result = await openclaw.post_content(
        content="测试推文：这是来自 X-Agent 的自动发帖 🚀",
        niche="general"
    )
    assert result["success"]
    print(f"✅ 发帖成功: {result['post_id']}")

    # 4. 测试评论（模拟）
    comment_result = await openclaw.comment_on_post(
        post_url="https://x.com/example/status/123",
        comment="这是一个有趣的话题！"
    )
    assert comment_result["success"]
    print(f"✅ 评论成功: {comment_result['comment_id']}")

asyncio.run(test_openclaw())
```

#### C. Telegram Bot 测试流程

```
1. 启动 Bot
   /start

2. 创建内容
   /create
   → 选择 A 类内容

3. 人工确认
   ✅ 人工确认发布

4. 二步确认
   ✓ 确认无误，发布

5. 观察日志
   [OpenClaw] ✅ 已通过 OpenClaw 发布
   Post ID: xxxxx
```

---

## 🛡️ 防封机制详解

### 规则 1: 随机延迟

```python
# 每次操作前，随机等待 10-40 秒
delay = random.uniform(DELAY_MIN, DELAY_MAX)
await asyncio.sleep(delay)

# 配置示例（宽松）：
DELAY_MIN=15
DELAY_MAX=60

# 配置示例（激进）：
DELAY_MIN=5
DELAY_MAX=15
```

**推荐值**:
- 🟢 安全：15-60 秒
- 🟡 平衡：10-40 秒（默认）
- 🔴 激进：5-15 秒（高风险）

### 规则 2: 内容变体

```python
# 自动添加 emoji 和短语，避免重复检测
原内容：  "AI is awesome"
变体后：  "AI is awesome 🚀 Just saying."

# 可自定义变体池（在 openclaw_bridge.py）
EMOJI_VARIANTS = ["🔥", "👀", "💡", "✨", "🚀"]
PHRASE_VARIANTS = ["Interesting.", "Thoughts?", "Just saying."]
```

### 规则 3: 每日上限

```python
# 严格限制每日操作数，避免异常行为
MAX_POSTS_PER_DAY = 5      # 每日最多 5 条推文
MAX_COMMENTS_PER_DAY = 15  # 每日最多 15 条评论
MAX_LIKES_PER_DAY = 30     # 每日最多 30 个赞
```

**推荐配置**:
```
类型          | 保守 | 平衡 | 激进
─────────────┼──────┼──────┼──────
发帖/天      | 2-3  | 5-7  | 10+
评论/天      | 5-10 | 15-20| 30+
点赞/天      | 10-20| 30-50| 100+
转发/天      | 2-5  | 5-10 | 20+
```

---

## 📊 监控和日志

### 查看实时日志

```bash
# 后台运行 X-Agent
pm2 logs x-agent | grep "OpenClaw"

# 或查看 Telegram Bot
# 向 Bot 发送 `/log` 命令查看操作记录
```

### OpenClaw 操作日志

```bash
# Docker 日志
docker logs -f openclaw_1

# 或访问 Dashboard
https://openclaw.io/dashboard/logs
```

### 监控指标

```python
# modules/monitor.py (可选创建)

async def get_daily_stats():
    """获取每日运营统计"""
    stats = {
        "posts_today": openclaw.post_count,
        "comments_today": openclaw.comment_count,
        "likes_today": openclaw.like_count,
        "post_limit": openclaw.daily_post_limit,
        "comment_limit": openclaw.daily_comment_limit,
    }
    return stats

# 在 Telegram Bot 中显示
/stats
→ 📊 今日统计
  发帖: 3/5
  评论: 12/15
  点赞: 28/30
```

---

## 🔐 生产环境部署

### 完整生产配置

```bash
# 1. 服务器准备（Linux/Ubuntu）
ssh root@your_server_ip

# 2. 克隆并配置
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent

# 3. 创建独立用户（安全最佳实践）
useradd -m -s /bin/bash xagent
su - xagent

# 4. Python 环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置环境变量（使用 systemd 管理）
sudo nano /etc/systemd/system/x-agent.service
```

**systemd 服务文件**:
```ini
[Unit]
Description=X-Agent with OpenClaw
After=network.target

[Service]
Type=simple
User=xagent
WorkingDirectory=/home/xagent/x-agent
EnvironmentFile=/home/xagent/x-agent/.env
ExecStart=/home/xagent/x-agent/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable x-agent
sudo systemctl start x-agent

# 查看状态
sudo systemctl status x-agent

# 查看日志
sudo journalctl -u x-agent -f
```

### 防火墙配置

```bash
# 如果使用本地 OpenClaw，确保端口开放
sudo ufw allow 8080/tcp

# Telegram Bot 连接需要出站 HTTPS
sudo ufw allow out 443/tcp
```

---

## ⚠️ 常见问题排查

### Q1: "OpenClaw API 连接失败"

```bash
# 检查清单
✓ OpenClaw 服务是否运行
  docker ps | grep openclaw
  或 ps aux | grep openclaw

✓ API 端点是否正确
  curl http://localhost:8080/health

✓ 防火墙规则
  sudo ufw status

✓ 日志输出
  pm2 logs x-agent | grep OpenClaw
```

### Q2: "每日限额已达"

```
原因：同一天内发帖/评论超过限制

解决：
1. 等待至明天（00:00 UTC 重置）
2. 或修改限额配置（更新 .env）
3. 检查是否有自动化任务重复运行
```

### Q3: "账户被限制"

```
症状：发帖失败，提示 "Account action required"

原因：可能被 X 检测为异常行为

解决：
1. 立即暂停自动化（设置所有开关为 false）
2. 手动登录 X，完成安全验证
3. 等待 24 小时
4. 重新配置更保守的防封参数
   - DELAY_MIN=30, DELAY_MAX=120
   - MAX_POSTS_PER_DAY=2
   - MAX_COMMENTS_PER_DAY=5
```

### Q4: "内容未被发布"

```
原因：可能是以下几种情况

1. 审核流程中止
   - 检查 Telegram 是否有待处理消息

2. OpenClaw 余额不足（付费版）
   - 检查 OpenClaw Dashboard 账户余额

3. 内容违规
   - 检查 risk_score
   - 人工审核内容合规性

4. 网络问题
   - 检查日志: `pm2 logs x-agent`
```

---

## 🎯 最佳实践

### 内容策略

```
✅ DO:
- 每日 2-5 条高质量原创推文
- 在最佳发布时间段发布
- 与受众互动（评论、转发）
- 使用相关的 hashtag 和 niche 语言
- 多样化内容类型（文字、图片、视频）

❌ DON'T:
- 一次性大量发布（触发限制）
- 重复发布相同内容（被检测为垃圾)
- 垃圾评论（自动回复每条推文）
- 自动点赞所有内容
- 频繁修改账户信息
```

### 监控周期

```
每日：
- 查看 /stats 统计
- 监控账户状态
- 检查是否有异常行为警告

每周：
- 分析内容表现（互动率）
- 调整发布时间表
- 优化 Niche 和内容质量

每月：
- 完整的增长报告
- 算法优化评估
- 防封机制有效性审计
```

---

## 📞 技术支持

| 资源 | 链接 |
|------|------|
| OpenClaw 官方文档 | https://docs.openclaw.io |
| X-Agent GitHub | https://github.com/sheldon010507-collab/x-agent |
| 问题报告 | https://github.com/sheldon010507-collab/x-agent/issues |
| 讨论区 | https://github.com/sheldon010507-collab/x-agent/discussions |

---

## 🎓 进阶应用

### 多账户管理

```python
# 如果想同时管理多个 X 账户

# 方案 1: 多个 OpenClaw 密钥
accounts = [
    {"name": "account_1", "api_key": "key_1"},
    {"name": "account_2", "api_key": "key_2"},
    {"name": "account_3", "api_key": "key_3"},
]

for account in accounts:
    openclaw = create_openclaw_bridge(
        api_key=account["api_key"]
    )
    # 发布内容...

# 方案 2: 使用 OpenClaw 的账户切换
openclaw.set_active_account("account_2")
await openclaw.post_content(content)
```

### 自定义防封规则

```python
# 根据内容类型调整防封参数

if content_type == "A类推文":
    # A 类风险低，可以激进一些
    delay = random.uniform(10, 30)

elif content_type == "B类脚本":
    # B 类通常带视频，需要更多时间
    delay = random.uniform(30, 60)

elif content_type == "C类评论":
    # C 类回复，延迟可以短一些
    delay = random.uniform(5, 15)

await asyncio.sleep(delay)
```

---

现在你已经拥有完整的部署指南！按照步骤逐一执行，就能成功部署 X-Agent + OpenClaw。🚀
