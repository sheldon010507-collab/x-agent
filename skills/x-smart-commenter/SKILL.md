# x-smart-commenter — X 智能评论 Skill

## 描述
智能 X (Twitter) 评论工具，支持自动生成评论、智能回复、防封机制。

## 功能
- 💬 智能评论生成
- 🎯 Niche 语气适配
- 🔄 评论变体
- ⏱️ 随机延迟（10-30秒）
- 📊 每日限额控制
- 🛡️ 防封机制

## 使用方法

### 基础调用
```python
from modules.openclaw_bridge import OpenClawBridge

bridge = OpenClawBridge()

# 智能评论
result = await bridge.comment(
    tweet_id="1234567890",
    niche="ai_tools"
)
```

### 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `tweet_id` | 推文 ID | 必填 |
| `niche` | Niche 模式 | general |
| `style` | 评论风格 | conversational |
| `delay` | 评论延迟 | 随机 10-30s |

## 评论风格

### conversational（对话式）
```
这个观点很有意思！我也在关注这个话题。
```

### analytical（分析式）
```
从技术角度看，这个方案有几个值得注意的点：
1. ...
2. ...
```

### supportive（支持式）
```
完全同意！这正是我一直想说的 🔥
```

### curious（好奇式）
```
好奇问一下，你是怎么发现这个的？想了解更多！
```

## 防封机制

### 1. 随机延迟
```python
# 每条评论延迟 10-30 秒
delay = random.uniform(10, 30)
```

### 2. 评论变体
```python
# 不同开头 + 不同结尾
prefixes = ["", "Hmm, ", "有趣的是，", "说实话，"]
suffixes = ["", " 🔥", " 👀", " 💡"]
```

### 3. 每日限额
```bash
# .env 配置
MAX_COMMENTS_PER_DAY=15
```

## Niche 语气

| Niche | 语气特点 |
|-------|---------|
| adult_uk | 幽默、直接、英国俚语 |
| ai_tools | 专业、前沿、tech 词汇 |
| beauty | 温暖、鼓励、emoji 丰富 |
| fitness | 激励、正能量、实用建议 |
| crypto | 分析、谨慎、数据驱动 |
| humor | 轻松、搞笑、梗 |
| custom | 自定义 |

## 配置

```bash
# .env
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_secret
MAX_COMMENTS_PER_DAY=15
```

## 智能回复逻辑

```
1. 分析推文内容和情绪
2. 选择合适的评论风格
3. 应用 Niche 语气
4. 生成评论变体
5. 检查是否重复
6. 添加随机延迟
7. 发布评论
```

## 错误处理

| 错误码 | 说明 | 处理 |
|--------|------|------|
| 429 | 频率限制 | 等待 15 分钟 |
| 404 | 推文不存在 | 跳过 |
| 403 | 无法评论 | 检查权限 |

## 版本
- v1.0.0 — 初始版本
- v2.0.0 — 添加智能回复
- v3.0.0 — OpenClaw 集成 + 防封
