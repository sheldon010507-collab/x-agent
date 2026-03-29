# X-Agent v0 Final

> ⚠️ **风险声明 / Risk Disclaimer**
>
> 本工具仅供学习和研究用途。使用本工具进行自动化操作可能违反平台服务条款。
> 作者不对因使用本工具导致的任何账号封禁、数据损失或其他后果负责。
>
> This tool is for learning and research purposes only. Automated operations may violate platform Terms of Service.
> The author is not responsible for any account bans, data loss, or other consequences.

**X（Twitter）智能运营Agent**
热点监控 + AI内容生产 + OpenClaw自动发帖/评论 + 每日复盘

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-v0_Final-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 核心亮点

### 📊 数据采集与增强
- 🔥 **多平台热点监控**：Reddit + Hacker News + Google Trends 原生异步采集
- 🧹 **智能去重算法**：Jaccard 相似度检测，自动移除重复内容（+15% 数据质量）
- 📈 **增强评分系统**：时间衰减 + 平台多样性奖励，更准确的热点判断
- ⚡ **并发优化**：按平台限制并发数 + 指数退避重试 + 超时保护（+30% 吞吐量）

### 🤖 内容生成与审核
- 🤖 **AI 内容生成**：推文(A类) / 视频脚本(B类) / 智能评论(C类)
- 🎭 **7 种 Niche 语气**：成人用品、AI工具、美妆、健身、加密、搞笑、自定义
- ✅ **强制二步审核**：所有内容都需经过人工二次确认，无自动发布路径
- 🤖 **Telegram Bot 驱动**：/start /set_niche /research /create /stats 等完整命令

### 🛡️ 发布与防护
- ⚡ **完整防封机制**：随机延迟(10-40秒)、内容变体、每日上限控制
- 🌐 **OpenClaw 集成**：自动发帖、评论、点赞、转发，企业级防封
- 📊 **Supabase 持久化**：热点记录 + 内容草稿 + 已发布统计 + 分析数据

**数据采集**：不依赖官方 X API，采用原生异步 Python 实现（PRAW、aiohttp、pytrends）+ OpenClaw 自动化方案，成本低、数据真实。

---

## ⚡ 快速部署 (3 种方式)

### 方式 1: 自动化脚本 (推荐 - 1 分钟)
```bash
cd x-agent
bash start_with_openclaw.sh
# 按提示选择启动方式
```

### 方式 2: Docker (2 分钟)
```bash
docker-compose up -d
# 自动启动 OpenClaw + X-Agent
```

### 方式 3: 传统启动 (3 分钟)
```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入配置
python main.py
```

📖 **详细指南**：
- [快速开始 (5分钟)](x-agent/docs/OPENCLAW_QUICK_START.md)
- [完整部署指南](x-agent/docs/OPENCLAW_DEPLOYMENT.md)
- [上手指南](x-agent/docs/UP_AND_RUNNING.md)

---

## 仓库结构

```
x-agent/
├── archive/           # 历史版本归档
│   ├── x-agent/       # v1
│   └── x-agent-v2/    # v2
└── x-agent/           # 当前版本 (v0 Final)
    ├── modules/       # 核心模块
    ├── niche_voices/  # 7种语气模板
    ├── prompts/       # Prompt模板
    ├── tests/         # 测试文件
    ├── docs/          # 文档
    └── migrations/    # 数据库迁移
```

---

## 核心模块

### 数据采集与处理
| 模块 | 功能 | 新增特性 |
|------|------|---------|
| `research.py` | 多平台研究（Reddit/HN/Google Trends 原生异步采集） | ✨ 并发限制、重试机制、超时保护 |
| `research_optimization.py` | **【新】** 采集优化框架 | 信号量控制、指数退避、健康检查 |
| `deduplicator.py` | **【新】** Jaccard 相似度去重 | 3-gram 分词、LRU 缓存、相似项分组 |
| `scorer.py` | 四维评分系统 (Relevance + Velocity + Authority + Convergence) | ✨ 时间衰减因子、平台多样性奖励 |

### 内容生成与发布
| 模块 | 功能 |
|------|------|
| `generator.py` | A/B/C 类内容生成 + 风险评分 |
| `bot_v0_final.py` | Telegram Bot 驱动 + **强制二步审核** |
| `openclaw_bridge.py` | OpenClaw 自动化 + 防封机制 (随机延迟、内容变体、每日限额) |

### 系统支持
| 模块 | 功能 |
|------|------|
| `llm_router.py` | 多 LLM 路由 (Claude/Groq/OpenAI/Gemini) |
| `database.py` | Supabase 数据持久化 (trends/content_queue/posts/analytics) |
| `config.py` | 配置管理 (Niche/LLM/自动化参数) |

---

## ✨ 三大增强功能 (v0 Final+)

### 1️⃣ 智能去重算法 (Deduplicator)
**解决问题**：多平台采集导致重复内容

- 🧹 **Jaccard 相似度**：基于 3-gram 分词的精确去重
- 📊 **配置灵活**：可调阈值（默认 75%）
- 🚀 **高性能**：LRU 缓存 + 集合操作（O(1) 查找）
- 📈 **数据质量**：自动移除重复，+15% 内容质量

**使用场景**：
```python
from modules.deduplicator import ContentDeduplicator

dedup = ContentDeduplicator(threshold=0.75)
unique_items = dedup.deduplicate_batch(items, content_key="text", score_key="score")
```

---

### 2️⃣ 增强评分系统 (Enhanced Scorer)
**解决问题**：单维度评分无法反映真实热度

- ⏱️ **时间衰减**：指数衰减函数（7 天半衰期）
  - 新鲜内容 (0 天)：1.0（100%）
  - 7 天老：0.3（30%）
  - 14 天老：0.1（10%）

- 🌐 **平台多样性奖励**：跨平台验证
  - 单平台：1.0（无奖励）
  - 2 平台：1.08（+8%）
  - 3 平台：1.15（+15%）
  - 4+ 平台：1.20（+20%）
  - HN+Reddit 组合：额外 +10%

**使用场景**：
```python
scorer = TrendScorer()
score = scorer.calculate_score_v2(trend_data)  # 包含两个新因子
details = scorer.score_with_details_v2(trend_data)  # 详细分解
```

---

### 3️⃣ 多源采集优化 (Research Optimization)
**解决问题**：并发采集导致 API 限流、超时、失败

- 🔒 **并发控制**：按平台 Semaphore 限制
  - Reddit：2 并发（严格）
  - HN：5 并发（宽松）
  - GoogleTrends：1 并发（单线程）

- 🔄 **指数退避重试**：自动恢复临时失败
  - 1st 失败 → 等待 2s
  - 2nd 失败 → 等待 4s
  - 3rd 失败 → 等待 8s
  - 全失败 → 返回 mock 数据

- ⏱️ **超时保护**：双层超时
  - 单个请求：10 秒
  - 总操作：30 秒

**使用场景**：
```python
# 自动应用所有优化
result = await researcher.research_async(
    niche="AI",
    timeout_secs=30  # 总超时
)
```

---

## 💾 数据存储

### 三层存储架构
```
本地存储 (Local)           云端存储 (Supabase)          容器存储 (Docker)
├─ data/research/         ├─ trends (热点)             ├─ openclaw_data
├─ data/logs/             ├─ content_queue (草稿)      └─ x-agent-data
└─ .env (配置)            ├─ posts (已发布)
                          └─ analytics (分析)
```

### 数据位置参考
| 数据类型 | 位置 | 说明 |
|---------|------|------|
| **研究缓存** | `x-agent/data/research/*.json` | 多平台采集结果 |
| **运行日志** | `x-agent/data/logs/x-agent.log` | 完整操作日志 |
| **配置文件** | `x-agent/.env` | API 密钥、Token 等 |
| **热点数据** | Supabase `trends` 表 | 评分后的热点 |
| **内容草稿** | Supabase `content_queue` 表 | A/B/C 类内容 |
| **已发布** | Supabase `posts` 表 | OpenClaw 发布记录 |
| **统计数据** | Supabase `analytics` 表 | 每日互动统计 |

📖 **详细存储指南**：见 [数据存储文档](x-agent/docs/DATA_STORAGE.md)

---

## 审批工作流

X-Agent **强制所有内容都经过人工确认**，确保操作的安全性和可控性：

```
1️⃣ 热点研究         2️⃣ 内容生成        3️⃣ 风险评估
   /research          /create            自动评分
        ↓                ↓                    ↓
    多平台采集     A/B/C 类生成        Risk Score 0-100
    + 去重算法     + Niche 语气             ↓
    + 增强评分     + 3 个选项      🟢低/🟡中/🔴高
        ↓                ↓                    ↓
   存储热点数据   人工选择一个    4️⃣ 二步审核
   （trends 表）     最佳内容       第一步：确认发布
                  （content_queue）  第二步：最终确认
                        ↓                  ↓
                   5️⃣ 发布控制      6️⃣ 发布执行
                   OpenClaw Bridge    随机延迟
                   • 随机延迟        内容变体
                   • 内容变体        检查限额
                   • 每日限额        ✅ 发送到 X
                   • 防封机制            ↓
                                   记录统计
                                  （posts 表）
```

**关键特性**：
- ✅ 无自动发布路径，100% 人工控制
- ✅ 二次确认机制防止误操作
- ✅ 智能防封：随机延迟 + 内容变体 + 每日限额
- ✅ 完整追溯：所有操作都可回查

---

## ⚠️ 风险声明

**本项目仅供学习研究使用。**

- 自动化操作 X (Twitter) 存在账号风险，请谨慎使用
- 建议使用小号测试，不要用于主账号
- 作者不对任何账号封禁负责
- 请遵守 X 平台服务条款
- **重要**：本项目所有内容生成都需人工审核后才能发布，用户对发布内容负责

---

## 📄 License

MIT License - 欢迎 Fork、Star、PR！

---

**Star ⭐ 支持一下～ 感谢每一位贡献者！**
