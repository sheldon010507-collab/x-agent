# X-Agent 与 OpenClaw 集成架构设计

**版本**: v1.0
**日期**: 2026-03-30
**配置者**: Wendy (Glasgow)
**开发者**: Claude Code

---

## 1. 整体架构

### 系统拓扑

```
┌─────────────────────────────────────────────────────────────┐
│                        Telegram                             │
│  (两个独立的 Bot)                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼──────────┐          ┌──────▼──────────┐
   │ OpenClaw Bot  │          │  X-Agent Bot    │
   │ (8649791429)  │          │  (8776781867)   │
   └────┬──────────┘          └──────┬──────────┘
        │                            │
        │                    ┌───────▼──────────┐
        │                    │  X-Agent API     │
        │                    │  (FastAPI)       │
        │                    │  Port: 8000      │
        │                    │                  │
        │                    │  ├─ /trends      │
        │                    │  ├─ /create      │
        │                    │  ├─ /report      │
        │                    │  └─ /health      │
        │                    └───────┬──────────┘
        │                            │
        │                    ┌───────▼──────────────┐
        │                    │  X-Agent Core Engine │
        │                    │                      │
        │                    │  ├─ Research Module  │
        │                    │  ├─ Scorer           │
        │                    │  ├─ Generator        │
        │                    │  ├─ Deduplicator     │
        │                    │  └─ Report Engine    │
        │                    └───────┬──────────────┘
        │                            │
        │                    ┌───────▼──────────┐
        │                    │    Supabase      │
        │                    │  (trends, posts) │
        │                    └──────────────────┘
        │
   ┌────▼──────────────────────────────────────┐
   │   OpenClaw Agent                           │
   │   (智能协调中心)                            │
   │                                            │
   │   主要职责:                                 │
   │   1. 理解用户 Telegram 消息                  │
   │   2. 调用 X-Agent API                      │
   │   3. 处理交互流程                           │
   │   4. 定时触发每日任务                       │
   │   5. 维护对话上下文                         │
   └────────────────────────────────────────────┘
```

---

## 2. 数据流示例

### 场景 A: 用户要求获取今日热点

```
用户 (Telegram)
    │
    ├─→ "给我看看今天的热点"
    │
用户 → OpenClaw Bot
    │
    └─→ OpenClaw Agent (理解意图)
         │
         ├─→ 调用 X-Agent API: GET /trends?niche=crypto&days=7
         │
    X-Agent API (FastAPI)
         │
         ├─→ research_async() ─┐
         │                      ├─→ 收集 Reddit/HN/Google Trends
         │                      ├─→ 去重 (Deduplicator)
         │                      └─→ 评分 (Scorer)
         │
         └─→ 返回 JSON: { trends: [...] }
              │
         OpenClaw Agent
              │
              ├─→ 格式化为 Markdown
              └─→ 发送回 Telegram

用户 ← Telegram
    │
    └─→ 📊 **今日热点 (Top 5)**
        1. AI Agent 自动化 - 评分: 89
        2. Telegram Bot 商业化 - 评分: 78
        ...
```

### 场景 B: 用户创建内容（二步审核）

```
用户: "给我生成一条关于 AI 的推文"
    │
    └─→ OpenClaw Agent
         │
         ├─→ POST /create_content
         │   {
         │     "niche": "ai_tools",
         │     "type": "A",
         │     "topic": "AI"
         │   }
         │
    X-Agent API
         │
         ├─→ research_async("ai_tools")
         ├─→ generate(research_result)
         └─→ 返回: {
         │     "content": "...",
         │     "risk_score": 45,
         │     "type": "A"
         │   }
         │
         OpenClaw Agent
         │
         ├─→ 显示内容 + 风险评分
         └─→ 等待用户二步确认

用户: "确认发布"
    │
    └─→ OpenClaw Agent
         │
         ├─→ POST /approve_content
         │   {
         │     "content_id": "123",
         │     "approved": true
         │   }
         │
    X-Agent API
         │
         ├─→ 保存到 Supabase
         └─→ 返回: { "success": true }
         │
         OpenClaw Agent
         │
         └─→ "✅ 内容已保存，可手动发布到 X"
```

### 场景 C: 每日自动日报

```
OpenClaw 定时任务 (每天 09:00 UTC)
    │
    └─→ GET /daily_report
         │
    X-Agent API
         │
         ├─→ 从 Supabase 读取今日数据
         │   ├─ 发布内容数
         │   ├─ 互动数据
         │   ├─ 最高评分内容
         │   └─ 趋势分析
         │
         ├─→ 生成 Markdown 报告
         └─→ 返回报告文本
              │
         OpenClaw Agent
              │
              └─→ 通过 Telegram 发送给用户
```

---

## 3. X-Agent 改造（FastAPI 化）

### 3.1 新增文件结构

```
x-agent/
├── main.py                     ← 现有 Bot 入口（保持不变）
├── api.py                      ← 【新增】FastAPI 服务器
├── cli.py                      ← 【新增】CLI 工具（本地调试）
├── requirements.txt            ← 添加 fastapi, uvicorn
└── modules/
    ├── research.py             ← 保持不变
    ├── scorer.py               ← 保持不变
    ├── generator.py            ← 保持不变
    ├── deduplicator.py         ← 保持不变
    ├── llm_router.py           ← 保持不变
    └── ...
```

### 3.2 FastAPI 端点设计

| 端点 | 方法 | 功能 | 输入 | 输出 |
|------|------|------|------|------|
| `/health` | GET | 健康检查 | 无 | `{"status": "ok"}` |
| `/trends` | GET | 获取热点 | `niche`, `days` | `{"trends": []}` |
| `/create` | POST | 生成内容 | `niche`, `type` | `{"content": "...", "risk_score": 45}` |
| `/approve` | POST | 确认发布 | `content_id` | `{"success": true}` |
| `/daily_report` | GET | 每日日报 | `date` (可选) | `{"report": "..."}` |
| `/status` | GET | 系统状态 | 无 | `{"db": "ok", "llm": "ok", ...}` |

### 3.3 请求/响应示例

#### GET /trends
```json
// 请求
GET /trends?niche=crypto&days=7

// 响应 (200)
{
  "status": "success",
  "trends": [
    {
      "topic": "Bitcoin ETF",
      "score": 89.5,
      "sources": ["reddit", "hackernews"],
      "summary": "Bitcoin spot ETF approval discussion",
      "created_at": "2026-03-30T10:00:00Z"
    },
    ...
  ],
  "total": 15,
  "timestamp": "2026-03-30T12:30:00Z"
}
```

#### POST /create
```json
// 请求
POST /create
{
  "niche": "ai_tools",
  "type": "A",
  "topic": "AI Agents",
  "research_days": 7
}

// 响应 (200)
{
  "status": "success",
  "content_id": "evt_123456",
  "type": "A",
  "content": "🤖 AI Agents are revolutionizing automation...",
  "risk_score": 42,
  "sources": ["reddit", "hackernews", "google_trends"],
  "research_summary": "Positive sentiment across 3 platforms",
  "timestamp": "2026-03-30T12:35:00Z"
}
```

#### GET /daily_report
```json
// 请求
GET /daily_report?date=2026-03-30

// 响应 (200)
{
  "status": "success",
  "date": "2026-03-30",
  "report": "📊 **今日复盘报告**\n\n📈 **热点监控**\n- 监控来源: 3 (Reddit, HN, Google Trends)\n- 发现趋势: 12 个\n- 平均评分: 71.3\n\n✍️ **内容生成**\n- A 类内容: 3 条 (已保存)\n- B 类内容: 2 条 (已保存)\n- C 类内容: 0 条\n\n🔥 **热门内容**\n1. \"AI Agents\" - 评分: 89, 来源: 3 个\n...",
  "stats": {
    "trends_found": 12,
    "content_generated": 5,
    "avg_score": 71.3
  }
}
```

---

## 4. OpenClaw Agent 设计

### 4.1 Agent 配置文件

位置: `C:\Users\wd010\.openclaw\workspace\agents\xagent\agent.json`

```json
{
  "name": "X-Agent Bot",
  "description": "热点监控、内容生成和自动化发布的智能助手",
  "icon": "🤖",
  "version": "1.0.0",

  "capabilities": [
    "trends_analysis",
    "content_generation",
    "daily_reporting",
    "conversation"
  ],

  "tools": [
    {
      "id": "get_trends",
      "name": "获取热点",
      "description": "从多平台实时获取最新热点",
      "endpoint": "http://x-agent:8000/trends",
      "method": "GET",
      "parameters": [
        {
          "name": "niche",
          "type": "string",
          "description": "领域 (crypto, ai_tools, beauty, etc)",
          "default": "general"
        },
        {
          "name": "days",
          "type": "integer",
          "description": "回溯天数",
          "default": 7
        }
      ]
    },

    {
      "id": "create_content",
      "name": "创建内容",
      "description": "生成 A/B/C 类内容",
      "endpoint": "http://x-agent:8000/create",
      "method": "POST",
      "parameters": [
        {
          "name": "niche",
          "type": "string",
          "description": "内容领域"
        },
        {
          "name": "type",
          "type": "enum",
          "enum": ["A", "B", "C"],
          "description": "A: 推文 | B: 视频脚本 | C: 评论"
        },
        {
          "name": "topic",
          "type": "string",
          "description": "创作主题"
        }
      ]
    },

    {
      "id": "daily_report",
      "name": "每日日报",
      "description": "生成今日数据总结",
      "endpoint": "http://x-agent:8000/daily_report",
      "method": "GET",
      "parameters": [
        {
          "name": "date",
          "type": "date",
          "description": "日期 (YYYY-MM-DD)",
          "default": "today"
        }
      ]
    }
  ],

  "systemPrompt": `你是 X-Agent 智能助手，专门处理热点监控和内容生成。

用户可能会问你：
1. "给我看看今天的热点" → 调用 get_trends
2. "生成一条关于 AI 的推文" → 调用 create_content (type=A)
3. "今日日报" → 调用 daily_report

回应时要：
- 友善、专业
- 清楚地展示数据
- 对生成的内容进行简短评论
- 如有风险评分 ≥80，要提醒用户
`,

  "triggers": [
    {
      "id": "daily_report_trigger",
      "name": "每日早报",
      "schedule": "0 9 * * *",  // UTC 09:00
      "action": "send_daily_report",
      "description": "每天早上 9 点自动发送日报"
    },
    {
      "id": "weekly_summary_trigger",
      "name": "周总结",
      "schedule": "0 17 * * MON",  // 周一 17:00
      "action": "send_weekly_summary",
      "description": "每周一晚上自动发送周总结"
    }
  ],

  "conversationStyle": {
    "tone": "professional_casual",
    "language": "chinese_traditional",
    "emoji": true,
    "markdown": true
  }
}
```

### 4.2 Agent 实现逻辑（伪代码）

```typescript
// openclaw-agent.ts
class XAgentBot {
  private xAgentAPI = "http://x-agent:8000";
  private telegramChannel: TelegramChannel;

  async handleMessage(message: string, userId: string) {
    const intent = this.parseIntent(message); // NLP 理解用户意图

    switch (intent.type) {
      case "TRENDS":
        return await this.getTrends(intent.niche, intent.days);

      case "CREATE_CONTENT":
        return await this.createContent(intent.niche, intent.type, intent.topic);

      case "DAILY_REPORT":
        return await this.getDailyReport(intent.date);

      case "HELP":
        return await this.showHelp();

      default:
        return "我没听懂，请试试:\n- 给我看看热点\n- 生成一条推文\n- 今日日报";
    }
  }

  async getTrends(niche: string, days: number) {
    const response = await fetch(
      `${this.xAgentAPI}/trends?niche=${niche}&days=${days}`
    );
    const data = await response.json();

    // 格式化为 Telegram 消息
    const message = `📊 **${niche} 领域热点 (近 ${days} 天)**\n\n`;
    data.trends.forEach((trend, idx) => {
      message += `${idx+1}. **${trend.topic}** (评分: ${trend.score})\n`;
    });

    await this.telegramChannel.send(message);
  }

  async createContent(niche: string, type: string, topic: string) {
    const response = await fetch(`${this.xAgentAPI}/create`, {
      method: "POST",
      body: JSON.stringify({ niche, type, topic })
    });
    const result = await response.json();

    // 第一步：显示生成的内容
    let message = `✍️ **已生成 ${type} 类内容**\n\n`;
    message += `${result.content}\n\n`;
    message += `⚠️ **风险评分**: ${result.risk_score}/100\n`;

    if (result.risk_score >= 80) {
      message += `🔴 **高风险！请谨慎审核**\n`;
    }

    // 显示审核按钮
    await this.telegramChannel.send(message, {
      buttons: [
        { text: "✅ 人工确认", action: "approve", contentId: result.content_id },
        { text: "🔄 重新生成", action: "regenerate" },
        { text: "❌ 跳过", action: "skip" }
      ]
    });
  }

  async getDailyReport(date?: string) {
    const response = await fetch(
      `${this.xAgentAPI}/daily_report?date=${date || 'today'}`
    );
    const data = await response.json();

    await this.telegramChannel.send(data.report);
  }

  // 定时任务：每天 09:00 UTC
  @Cron("0 9 * * *")
  async sendDailyReport() {
    await this.getDailyReport();
  }
}
```

---

## 5. Docker Compose 更新

### 5.1 新增 x-agent 服务

```yaml
# 在现有 docker-compose.yml 中添加

services:
  x-agent:
    image: python:3.12-slim
    container_name: x-agent-api
    working_dir: /app/x-agent
    command: >
      sh -c "pip install -r requirements.txt -q &&
             python3 -m uvicorn api:app --host 0.0.0.0 --port 8000"

    volumes:
      # 挂载 x-agent 源代码
      - ${OPENCLAW_WORKSPACE_DIR}/agents/xagent/x-agent:/app/x-agent
      # 挂载配置文件
      - ${OPENCLAW_CONFIG_DIR}/xagent.env:/app/x-agent/.env

    environment:
      # 从主 .env 继承
      TELEGRAM_BOT_TOKEN: ${XAGENT_TELEGRAM_BOT_TOKEN}
      TELEGRAM_CHAT_ID: ${XAGENT_TELEGRAM_CHAT_ID}
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_KEY: ${SUPABASE_KEY}
      LLM_PROVIDER: nvidia
      LLM_MODEL: z-ai/glm5
      NVIDIA_NIM_API_KEY: ${NVIDIA_NIM_API_KEY}
      NVIDIA_NIM_BASE_URL: https://integrate.api.nvidia.com/v1
      # FastAPI 特定
      PYTHONUNBUFFERED: "1"
      LOG_LEVEL: "info"

    ports:
      - "8000:8000"  # FastAPI 端口

    networks:
      - openclaw-net  # 加入 OpenClaw 网络

    restart: unless-stopped

    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    depends_on:
      openclaw-gateway:
        condition: service_healthy

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # 【可选】OpenClaw Agent 服务（与 openclaw-cli 相同网络）
  openclaw-xagent:
    image: ${OPENCLAW_IMAGE:-openclaw:local}
    network_mode: "service:openclaw-gateway"
    cap_drop:
      - NET_RAW
      - NET_ADMIN
    security_opt:
      - no-new-privileges:true
    environment:
      HOME: /home/node
      TERM: xterm-256color
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN:-}
      XAGENT_API_URL: "http://x-agent:8000"  # 访问 X-Agent API
      XAGENT_API_KEY: ${XAGENT_API_KEY:-}
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw
      - ${OPENCLAW_WORKSPACE_DIR}:/home/node/.openclaw/workspace
    stdin_open: true
    tty: true
    init: true
    entrypoint: ["node", "dist/index.js"]
    depends_on:
      - openclaw-gateway
      - x-agent
```

### 5.2 .env 文件更新

```env
# 原有配置...

# ========== X-Agent 配置 ==========
XAGENT_TELEGRAM_BOT_TOKEN=replace_with_token_from_botfather
XAGENT_TELEGRAM_CHAT_ID=8749189654

# X-Agent API 密钥（可选）
XAGENT_API_KEY=your_secret_key_here

# Supabase
SUPABASE_URL=https://gqpsgrzxzkphxxlkqhor.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 6. 实施时间表

| 阶段 | 任务 | 时间 | 负责 |
|------|------|------|------|
| **Phase 1** | X-Agent FastAPI 化 | 4 小时 | Claude Code |
| | - 创建 `api.py` | | |
| | - 实现 5 个核心端点 | | |
| | - 添加错误处理和日志 | | |
| | - 创建 `Dockerfile` | | |
| **Phase 2** | 本地测试 | 2 小时 | Claude Code |
| | - 启动 FastAPI 服务 | | |
| | - 测试所有端点 | | |
| | - 性能和负载测试 | | |
| **Phase 3** | OpenClaw Agent 开发 | 6 小时 | Wendy |
| | - 创建 agent.json | | |
| | - 实现 TypeScript 逻辑 | | |
| | - 定时任务配置 | | |
| **Phase 4** | 集成测试 | 2 小时 | 双方 |
| | - 通过 Telegram 测试 | | |
| | - 二步审核流程测试 | | |
| | - 每日日报自动化测试 | | |
| **Phase 5** | 部署上线 | 1 小时 | Wendy |
| | - 更新 docker-compose.yml | | |
| | - 启动所有服务 | | |
| | - 监控运行状态 | | |

**总计**: 15 小时（分散在 2-3 天）

---

## 7. 风险评估和注意事项

| 风险 | 影响 | 缓解方案 |
|------|------|--------|
| X-Agent API 超时 | 用户体验差 | 添加请求超时 (30s) + 异步队列 |
| Supabase 连接失败 | 无法读写数据 | 重试机制 + 本地缓存 |
| NVIDIA API 限流 | 内容生成失败 | 降级到本地模型或 fallback |
| OpenClaw Agent 崩溃 | 无法交互 | 自动重启 + 监控告警 |
| Telegram Bot 冲突 | 消息混乱 | 使用不同的 Bot Token |

---

## 8. 成功标志

✅ Phase 完成的条件：

**Phase 1**: FastAPI 服务启动，所有端点返回 200 OK
**Phase 2**: 本地 cURL 请求成功，数据格式正确
**Phase 3**: OpenClaw Agent 配置文件有效，可以被 OpenClaw 识别
**Phase 4**: 通过 Telegram 成功调用全部功能，二步审核工作正常
**Phase 5**: Docker 容器全部 Running，无错误日志，自动日报按时发送

---

## 9. 后续扩展可能性

- 🎨 支持图片生成
- 📱 多平台发布（TikTok, Instagram）
- 🔔 智能推送通知
- 📊 完整的分析仪表板
- 🤝 多用户协作
- 🌐 国际化支持（多语言）

---

**联系信息**:
- 开发: Claude Code (claude.ai/code)
- 配置: Wendy (Glasgow)
- 项目: sheldon010507-collab/x-agent
