# x-poster — X 平台自动发帖 Skill

## 描述
智能 X (Twitter) 发帖工具，支持内容生成、自动发布、防封机制。

## 功能
- 📝 自动生成推文内容
- 🔄 内容变体（避免重复检测）
- ⏱️ 随机延迟（防封）
- 📊 每日限额控制
- 🎯 多 Niche 支持

## 使用方法

### 基础调用
```python
from modules.openclaw_bridge import OpenClawBridge

bridge = OpenClawBridge()

# 发布推文
result = await bridge.post(
    content="AI 工具推荐：这款新工具太强了！🔥",
    niche="ai_tools"
)
```

### 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `content` | 推文内容 | 必填 |
| `niche` | Niche 模式 | general |
| `auto_variant` | 自动变体 | True |
| `delay` | 发布延迟 | 随机 8-25s |

## 防封机制

### 1. 随机延迟
```python
# 每条推文延迟 8-25 秒
delay = random.uniform(8, 25)
```

### 2. 内容变体
```python
# 自动添加不同 emoji
emojis = ["🔥", "👀", "💡", "✨", "🚀"]
content = content + " " + random.choice(emojis)
```

### 3. 每日限额
```bash
# .env 配置
MAX_POSTS_PER_DAY=10
```

## 内容类型

### A 类：热点推送
```
🔥 Breaking: {topic}
{summary}
#hashtag
```

### B 类：深度分析
```
关于 {topic} 的深度分析：
{insights}
👇 详细内容
```

### C 类：互动评论
```
{comment}
#hashtag
```

## 配置

```bash
# .env
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
MAX_POSTS_PER_DAY=10
```

## 错误处理

| 错误码 | 说明 | 处理 |
|--------|------|------|
| 429 | 频率限制 | 等待 15 分钟 |
| 401 | 认证失败 | 检查 API Key |
| 403 | 权限不足 | 检查权限设置 |

## 版本
- v1.0.0 — 初始版本
- v2.0.0 — 添加防封机制
- v3.0.0 — OpenClaw 集成
