# OpenClaw 快速启动指南 (5 分钟)

## 🎯 目标
在 5 分钟内让 X-Agent + OpenClaw 跑起来

---

## 📋 前置条件清单

- [ ] Python 3.11+
- [ ] Node.js（用于 PM2）或 Docker
- [ ] OpenClaw 账户 + API 密钥
- [ ] Telegram Bot Token
- [ ] X/Twitter 账户已关联到 OpenClaw

---

## ⚡ 快速启动（3 种方式）

### 方式 A: 自动化脚本（推荐）

```bash
cd x-agent

# 一行命令启动
bash start_with_openclaw.sh

# 按提示选择启动方式
# 选择 1（前台）或 2（PM2 后台）
```

✨ **这个脚本会自动：**
- ✅ 检查 Python 版本
- ✅ 创建虚拟环境
- ✅ 安装依赖
- ✅ 检查环境变量
- ✅ 启动服务

---

### 方式 B: 手动启动（5 步）

```bash
# 1. 进入项目
cd x-agent

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
nano .env  # 编辑填入配置

# 5. 启动
python main.py
```

---

### 方式 C: Docker（最简单）

```bash
# 1. 启动 OpenClaw
docker-compose up -d openclaw

# 2. 构建 X-Agent
docker build -t x-agent .

# 3. 运行 X-Agent
docker run -d --env-file .env x-agent
```

---

## 🔧 配置 .env （5 个必需项）

```env
# OpenClaw API
OPENCLAW_API_KEY=xxx_from_dashboard
OPENCLAW_API_ENDPOINT=http://localhost:8080

# Telegram
TELEGRAM_BOT_TOKEN=xxx_from_botfather

# Supabase (数据库)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx_service_role_key

# LLM (AI 模型)
ANTHROPIC_API_KEY=sk-xxx
```

📖 **详细配置**: 见 `OPENCLAW_DEPLOYMENT.md` 的 "Step 2"

---

## ✅ 验证部署

### 检查 OpenClaw 连接
```bash
curl http://localhost:8080/health
# 应返回: {"status":"ok"}
```

### 检查 Telegram Bot
```
在 Telegram 中发送给你的 Bot:
/start
# 应该看到欢迎消息
```

### 完整工作流测试
```
1. /create          → 创建内容
2. 选择内容类型     → A/B/C
3. ✅ 人工确认发布  → 点击按钮
4. ✓ 确认无误，发布 → 再点一次
5. 查看日志          → 应该看到发帖成功
```

---

## 📊 常用命令

| 命令 | 说明 |
|------|------|
| `pm2 logs x-agent` | 查看实时日志 |
| `pm2 restart x-agent` | 重启服务 |
| `pm2 stop x-agent` | 停止服务 |
| `/stats` | Telegram 中查看统计 |
| `/settings` | 调整防封参数 |

---

## 🚨 常见错误及快速修复

| 错误 | 原因 | 修复 |
|------|------|------|
| `OpenClaw API not reachable` | OpenClaw 未运行 | `docker-compose up -d` |
| `TELEGRAM_BOT_TOKEN invalid` | Token 错误 | 检查 .env 文件 |
| `Account action required` | 账户被限制 | 等 24h，调整防封参数 |
| `Daily limit exceeded` | 超过每日限额 | 等待明天或修改 MAX_*_PER_DAY |

---

## 🎮 在 Telegram Bot 中测试

```
/start                  ← 查看欢迎信息
/create                 ← 创建内容
  → 选择 A 类推文
  → AI 生成 3 条选项
  → 选择最好的一条
  ✅ 人工确认发布
    → ✓ 确认无误，发布
      → 通过 OpenClaw 发送到 X
      → ✅ 发帖成功!

/stats                  ← 查看今日统计
/settings               ← 调整参数
```

---

## 📈 部署后的下一步

| 步骤 | 内容 |
|------|------|
| **1. 热点监控** | `/research` 命令研究热点 |
| **2. 内容策略** | `/strategy` 查看营运策略 |
| **3. 性能优化** | 根据 `/stats` 调整参数 |
| **4. 多账户** | 配置多个 OpenClaw 密钥 |

---

## 🔐 生产环境检查清单

- [ ] 使用强密码保护 OpenClaw 账户
- [ ] 定期检查 X 账户活动日志
- [ ] 监控每日限额使用情况
- [ ] 设置日志轮转（避免磁盘满）
- [ ] 配置告警（超限时通知）

---

## 📞 获取帮助

| 资源 | 链接 |
|------|------|
| **完整部署文档** | `docs/OPENCLAW_DEPLOYMENT.md` |
| **代码示例** | `examples/openclaw_examples.py` |
| **测试文件** | `tests/test_openclaw_integration.py` |
| **GitHub Issues** | https://github.com/sheldon010507-collab/x-agent/issues |

---

## 🎓 进阶用法

### 多账户管理
```bash
# 为不同 X 账户创建多个部署
# 使用不同的 OPENCLAW_API_KEY
```

### 自定义防封规则
```python
# 在 bot_v0_final.py 中修改
DELAY_MIN=30  # 更保守
MAX_POSTS_PER_DAY=2
```

### 数据分析
```bash
# 查询 Supabase 中的发帖历史
SELECT * FROM posts WHERE created_date = TODAY()
```

---

## 💡 最佳实践

✅ **DO:**
- 从低频率开始（1-2 条/天）
- 监控账户健康状况
- 定期查看互动数据
- 根据反馈调整内容

❌ **DON'T:**
- 一次性大量发帖（触发限制）
- 频繁修改防封参数
- 忽视日志告警
- 使用禁止内容

---

## ⏱️ 时间表

| 时间 | 任务 |
|------|------|
| **0-5 分钟** | 按本指南快速启动 |
| **5-30 分钟** | 在 Telegram 中测试工作流 |
| **30 分钟-1 小时** | 验证内容在 X 上发布成功 |
| **1 天** | 观察账户状态和互动 |
| **1 周** | 第一次性能分析和优化 |

---

**🎉 完成！您的 X-Agent + OpenClaw 已启动！**

现在发送 `/start` 给你的 Telegram Bot 开始使用吧 🚀
