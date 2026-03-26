# x-research — X 平台深度研究 Skill

## 描述
多平台热点深度研究，支持 X (Twitter)、Reddit、YouTube、Hacker News、Web、TikTok、Instagram、Bluesky、Polymarket 等平台的数据采集和分析。

## 功能
- 🔍 多平台搜索和数据采集
- 📊 4维评分（Relevance + Velocity + Authority + Convergence）
- 📝 热点摘要生成
- 🔗 引用来源追踪
- 💾 本地缓存支持

## 使用方法

### 基础调用
```bash
last30days "AI tools" --days=7 --sources=x,reddit,youtube
```

### 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 研究话题 | 必填 |
| `--days` | 回溯天数 | 7 |
| `--sources` | 数据源列表 | 全平台 |
| `--agent` | Agent 模式 | 关闭 |
| `--output` | 输出格式 | json |

### 输出格式
```json
{
  "relevance_score": 75.5,
  "velocity_24h": 60.2,
  "authority_score": 55.0,
  "platform_count": 4,
  "summary": "热点摘要...",
  "citations": [...],
  "trends": [...]
}
```

## 数据源
- **x** — X (Twitter)
- **reddit** — Reddit
- **youtube** — YouTube
- **hn** — Hacker News
- **web** — Web 搜索
- **tiktok** — TikTok
- **ig** — Instagram
- **bluesky** — Bluesky
- **polymarket** — Polymarket

## 集成示例

### Python
```python
from modules.research import research_topic

result = research_topic(
    niche="AI tools",
    days=7,
    sources="x,reddit,youtube"
)

print(f"相关性: {result['relevance_score']}")
print(f"增速: {result['velocity_24h']}")
```

### OpenClaw 调用
```python
from modules.openclaw_bridge import OpenClawBridge

bridge = OpenClawBridge()
research = await bridge.research("AI tools")
```

## 配置

在 `.env` 中配置：
```bash
LAST30DAYS_API_KEY=your_api_key
LAST30DAYS_API_ENDPOINT=https://api.last30days.com
```

## 注意事项
- API 调用有频率限制，建议添加缓存
- 24小时内相同话题会返回缓存结果
- 建议在低峰期执行大规模研究

## 版本
- v1.0.0 — 初始版本
- v2.0.0 — 添加 4D 评分
- v3.0.0 — OpenClaw 集成
