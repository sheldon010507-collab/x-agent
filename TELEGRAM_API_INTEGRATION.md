# Telegram Bot + X-Agent API 集成指南

## 📋 概述

将你的 Telegram Bot 与本地 X-Agent API 服务集成，实现通过 Telegram 直接控制内容生成、审核和发布。

## 🚀 快速开始

### 1️⃣ 确保 API 服务运行

```bash
docker compose up -d x-agent-api
```

检查健康状态：
```bash
curl http://localhost:8000/health
```

### 2️⃣ 在你的 Bot 中添加 API 命令

在你的 Bot 主文件中（例如 `main.py` 或 `bot_v0_final.py`）添加：

```python
from modules.api_client import XAgentAPIClient
from modules.bot_api_commands import BotAPICommands

# 初始化 API 客户端
api_client = XAgentAPIClient(api_url="http://localhost:8000")
bot_api_commands = BotAPICommands(api_client)

# 在 application 中注册命令处理器
application.add_handler(CommandHandler("api_status", bot_api_commands.cmd_api_status))
application.add_handler(CommandHandler("trends", bot_api_commands.cmd_api_trends))
application.add_handler(CommandHandler("generate", bot_api_commands.cmd_api_generate))
application.add_handler(CommandHandler("report", bot_api_commands.cmd_api_report))

# 注册回调处理（用于按钮点击）
application.add_handler(CallbackQueryHandler(bot_api_commands.handle_api_callback))
```

## 📱 可用的 Telegram 命令

### `/api_status` 
检查 API 服务状态

**响应示例：**
```
✅ API 状态正常

🔧 服务：x-agent-api
📦 版本：1.0.0
🎯 细分领域：general
⚙️ LLM：nvidia
⏰ 时间：2026-04-03T13:35:51
```

### `/trends [niche] [days]`
获取热点趋势

**用法示例：**
```
/trends general 7      # 获取通用领域最近7天的热点
/trends tech 30        # 获取科技领域最近30天的热点
/trends                # 使用默认参数（general, 7天）
```

**响应示例：**
```
📊 general 细分领域热点趋势（最近 7 天）

1. AI技术发展 (评分: 95)
2. 区块链应用 (评分: 88)
3. 云计算趋势 (评分: 85)
...
```

### `/generate <type> <topic>`
生成内容草稿

**用法示例：**
```
/generate A AI如何改变办公方式              # 生成推文
/generate B 5G技术对生活的影响             # 生成视频脚本
```

**参数说明：**
- `type`: 内容类型
  - `A` = 推文
  - `B` = 视频脚本
- `topic`: 话题（支持中英文）

**响应示例：**
```
✅ 推文生成成功

📝 ID: fe29ddc0-acb7-4766-861b-554a0b07c582
📌 状态: draft
📚 话题: AI技术发展

生成的推文数：3

1. Hot take: Unpopular opinion about AI🚀: it's more relevant than you think. 💭
...
```

**按钮操作：**
- ✅ 批准发布 - 确认内容，变更状态为 confirmed
- ❌ 删除 - 删除草稿

### `/report [date]`
获取每日报告

**用法示例：**
```
/report                   # 获取今天的报告
/report 2026-04-03       # 获取指定日期的报告
```

**响应示例：**
```
📊 每日报告

📅 日期: 2026-04-03
📝 帖子数: 3
💬 评论数: 0
❤️ 点赞数: 0
🔄 转发数: 0
⭐ 最高互动: 0
```

## 🔧 完整集成示例

### 在 `bot_v0_final.py` 中添加初始化代码

```python
from modules.api_client import XAgentAPIClient
from modules.bot_api_commands import BotAPICommands

class BotV0Final:
    def __init__(self, token: str, db, generator, llm_router):
        # ... 现有初始化代码 ...
        
        # 添加 API 客户端
        self.api_client = XAgentAPIClient(api_url="http://localhost:8000")
        self.api_commands = BotAPICommands(self.api_client)
    
    async def initialize(self) -> None:
        """初始化处理器"""
        # ... 现有代码 ...
        
        # 添加 API 命令处理器
        self.application.add_handler(
            CommandHandler("api_status", self.api_commands.cmd_api_status)
        )
        self.application.add_handler(
            CommandHandler("trends", self.api_commands.cmd_api_trends)
        )
        self.application.add_handler(
            CommandHandler("generate", self.api_commands.cmd_api_generate)
        )
        self.application.add_handler(
            CommandHandler("report", self.api_commands.cmd_api_report)
        )
        self.application.add_handler(
            CallbackQueryHandler(self.api_commands.handle_api_callback)
        )
```

### 在 `main.py` 中添加初始化代码

```python
from modules.api_client import XAgentAPIClient
from modules.bot_api_commands import BotAPICommands

class XAgentApp:
    async def initialize(self):
        # ... 现有初始化代码 ...
        
        # 5. 初始化 API 客户端
        self.api_client = XAgentAPIClient("http://localhost:8000")
        
        # 为 bot 添加 API 命令
        api_commands = BotAPICommands(self.api_client)
        
        # 在 bot 的 application 中注册命令
        # (需要从 bot 实例中访问 application)
```

## 🔌 API URL 配置

如果 API 运行在不同的机器或端口上，修改初始化代码：

```python
# 本地默认
api_client = XAgentAPIClient("http://localhost:8000")

# 远程服务器
api_client = XAgentAPIClient("http://192.168.1.100:8000")

# 自定义端口
api_client = XAgentAPIClient("http://localhost:9000")
```

## 📊 工作流程示例

1. **查看系统状态**
   ```
   /api_status
   ```

2. **获取热点**
   ```
   /trends general 7
   ```

3. **生成内容**
   ```
   /generate A AI技术发展趋势
   ```

4. **通过按钮批准**
   - 点击"✅ 批准发布"按钮

5. **查看统计**
   ```
   /report
   ```

## 🐛 故障排除

### API 连接失败

**错误信息：**
```
❌ API 离线：[Errno 111] Connection refused
```

**解决方案：**
```bash
# 检查 API 是否运行
docker ps | grep x-agent-api

# 查看 API 日志
docker logs x-agent-api

# 重启 API
docker compose restart x-agent-api
```

### 生成内容超时

**原因：** LLM API 响应缓慢

**解决方案：**
- 在 `api_client.py` 中修改超时时间
```python
self.client = httpx.AsyncClient(timeout=60.0)  # 改为 60 秒
```

### 数据库错误

**检查本地数据库：**
```bash
# 查看数据库大小
ls -lh x-agent/data/x_agent.db

# 备份数据库
cp x-agent/data/x_agent.db x-agent/data/x_agent.db.backup
```

## 📚 文件清单

创建的新文件：
- `x-agent/modules/api_client.py` - API HTTP 客户端
- `x-agent/modules/bot_api_commands.py` - Bot 命令处理器
- `TELEGRAM_API_INTEGRATION.md` - 本文档

修改的文件：
- `bot_v0_final.py` 或 `main.py` - 添加命令处理器注册

## 🎯 下一步

1. ✅ API 服务已运行（`docker compose up -d x-agent-api`）
2. 📝 在 Bot 中添加命令处理器
3. 🚀 启动 Bot，测试命令
4. 📊 监控日志输出
5. 🔄 持续优化提示词和 LLM 配置

## 💡 提示

- 所有命令都支持中文参数
- API 响应时间取决于 LLM 服务速度（通常 5-15 秒）
- 内容草稿保存在本地 SQLite 数据库中
- 可以在 Telegram 中并发生成多个内容

---

有问题？查看日志：
```bash
docker logs x-agent-api -f
```
