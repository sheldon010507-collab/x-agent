# X-Agent × OpenClaw 集成方案（简版）

## 核心概念

把 X-Agent 改造成 **HTTP API 服务** + **OpenClaw Agent 协调者**

```
Telegram 用户
    ↓
[OpenClaw Agent] ← 理解用户意图
    ↓
[X-Agent API] (FastAPI) ← 执行具体操作
    ↓
[核心引擎] ← 热点收集、评分、生成
    ↓
Supabase ← 数据存储
```

## 5 个关键 API 端点

| 端点 | 功能 | 示例 |
|------|------|------|
| `GET /trends` | 获取热点 | "给我看看热点" |
| `POST /create` | 生成内容 | "生成一条推文" |
| `POST /approve` | 确认发布 | "确认发布" |
| `GET /daily_report` | 每日日报 | "今日日报" |
| `GET /health` | 健康检查 | 监控用 |

## 5 个实施阶段

1. **FastAPI 化** (4h) - 把 X-Agent 改造为 API 服务
2. **本地测试** (2h) - 测试所有端点
3. **OpenClaw Agent** (6h) - Wendy 创建智能协调者
4. **集成测试** (2h) - Telegram 端到端测试
5. **上线部署** (1h) - Docker Compose 启动

**总计**: 15 小时（2-3 天）

## 优势

✅ X-Agent 核心逻辑不变（只打包成 API）
✅ 完全通过 Telegram 交互（无需学习新界面）
✅ 支持二步审核（安全）
✅ 自动每日日报
✅ 可后续扩展（图片、多平台等）

## 下一步

1. **Wendy 确认**：时间安排、资源可用性
2. **开始 Phase 1**：创建 api.py，实现 FastAPI
3. **持续协作**：定期测试、反馈调整

---

详细设计文档见: `OPENCLAW_INTEGRATION_ARCHITECTURE.md`
