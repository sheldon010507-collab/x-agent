# X-Agent 架构文档

## 组件架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        X-Agent System                           │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────┐    │
│  │  Telegram   │    │   Scheduler │    │  Research CLI    │    │
│  │  Bot (V0)   │    │  (APSchedul)│    │  (last30days)    │    │
│  └──────┬──────┘    └──────┬──────┘    └────────┬─────────┘    │
│         │                  │                     │              │
│         ▼                  ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   XAgentApp (main.py)                    │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│         ┌───────────────────┼────────────────────┐             │
│         ▼                   ▼                    ▼             │
│  ┌─────────────┐   ┌───────────────┐   ┌──────────────────┐   │
│  │  Researcher │   │ContentGenerator│  │   TrendScorer    │   │
│  │(research.py)│   │(generator.py) │   │  (scorer.py)     │   │
│  └──────┬──────┘   └───────┬───────┘   └──────────────────┘   │
│         │                  │                                    │
│         │                  ▼                                    │
│         │         ┌─────────────────┐                          │
│         │         │   LLMRouter     │                          │
│         │         │(llm_router.py)  │                          │
│         │         └────────┬────────┘                          │
│         │                  │                                    │
│         │    ┌─────────────┼──────────────┐                    │
│         │    ▼             ▼              ▼                    │
│         │  Anthropic    OpenAI          Groq                   │
│         │  Claude       (+ OR/NIM/      (fast)                 │
│         │               Ollama)                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐   ┌───────────────────┐                      │
│  │  Database    │   │  OpenClawBridge   │                      │
│  │(database.py) │   │(openclaw_bridge.py│                      │
│  │  Supabase    │   │  X/Twitter API)   │                      │
│  └──────────────┘   └───────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| 应用入口 | `main.py` | 初始化所有组件，统一 asyncio 事件循环 |
| Telegram Bot | `bot_v0_final.py` | 用户交互、命令处理、按钮回调 |
| 研究模块 | `research.py` | 调用 last30days CLI 获取热点数据 |
| 评分模块 | `scorer.py` | 热点综合评分，决定推送/存储/丢弃 |
| 生成模块 | `generator.py` | A/B/C 三类内容生成，注入 Niche 语气 |
| LLM 路由 | `llm_router.py` | 多供应商统一接口，支持 6 种 LLM |
| 数据库 | `database.py` | Supabase CRUD，内容状态流转 |
| 配置 | `config.py` | 环境变量加载，.env 管理 |
| OpenClaw | `openclaw_bridge.py` | X/Twitter 发帖、评论的防封桥接 |

## 数据流

```
热点发现 → 研究 → 评分 → 内容生成 → 人工审核 → 发布
  │           │       │        │           │         │
Research  Scorer  Generator  Telegram    Bot     OpenClaw
              ↕                           ↕
          Database ←────────────────── Database
```

## 内容状态机

```
         ┌──────────┐
         │  draft   │  ← 内容生成后默认状态
         └────┬─────┘
              │
       ┌──────┴──────┐
       ▼             ▼
┌──────────┐  ┌──────────┐
│confirmed │  │ rejected │
└────┬─────┘  └──────────┘
     │
     ▼
┌──────────┐
│published │  ← OpenClaw 发布成功后
└──────────┘
```

## 风险评分体系

风险评分范围：0 ~ 100，≥ 80 时禁止自动发布。

### 热点风险（`research.py`）

| 因素 | 影响 |
|------|------|
| 基础分 | +30 |
| 速度 velocity_24h > 80 | +20 |
| 平台数 < 3 | +15 |
| 权威度 authority_score < 40 | +15 |

### 内容风险（`generator.py`）

| 因素 | 影响 |
|------|------|
| 基础分 | +30 |
| A 类推文 | +10 |
| C 类评论 | +15 |
| 敏感关键词 | +20 |
| Crypto Niche | +20 |
| Adult Niche | +25 |

## 热点评分权重公式

```
Score = R×0.40 + V×0.30 + A×0.15 + C×0.15

其中:
  R = relevance_score（相关度）
  V = velocity_24h（24h 增速）
  A = authority_score（权威度）
  C = convergence（平台汇聚性，platform_count 映射）

platform_count → convergence:
  1 → 30, 2 → 50, 3 → 70, 4 → 85, 5+ → 100

决策阈值:
  ≥ 80 → PUSH_NOW（立即推送）
  60-79 → ADD_TO_DIGEST（加入摘要）
  50-59 → STORE（仅存储）
  < 50  → DISCARD（丢弃）
```
